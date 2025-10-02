# speed_analyzer.py
import cv2
import numpy as np
import logging
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)

class SpeedAnalyzer:
    def __init__(self, calibration_factor=None):
        """
        Initialize the speed analyzer.
        
        Args:
            calibration_factor: Pixels-to-meters conversion factor.
                If None, will attempt to auto-calibrate based on known disc diameter.
        """
        self.calibration_factor = calibration_factor  # pixels per meter
        self.disc_diameter = 0.21  # Standard disc golf disc is ~21cm diameter
        
    def auto_calibrate(self, frame, disc_contour):
        """
        Auto-calibrate using the disc as a reference object.
        Assumes the disc is a standard diameter disc golf disc.
        """
        if disc_contour is None or len(disc_contour) < 5:
            return False
        
        # Fit an ellipse to the disc contour
        ellipse = cv2.fitEllipse(disc_contour)
        axis_length = max(ellipse[1])  # Major axis in pixels
        
        # Calculate pixels per meter using known disc diameter
        self.calibration_factor = axis_length / self.disc_diameter
        logger.info(f"Auto-calibrated: {self.calibration_factor} pixels per meter")
        return True
    
    def calculate_release_speed(self, disc_positions, fps, release_frame_idx=None):
        """
        Calculate the disc speed at release.
        
        Args:
            disc_positions: List of (x, y, frame) tuples with disc positions
            fps: Frames per second of the video
            release_frame_idx: Index of the release frame if known, otherwise auto-detected
            
        Returns:
            Speed in m/s, km/h, and mph
        """
        if not disc_positions or len(disc_positions) < 3:
            logger.warning("Not enough disc positions to calculate speed")
            return None
            
        # Sort positions by frame
        disc_positions.sort(key=lambda pos: pos[2])
        frames = np.array([pos[2] for pos in disc_positions])
        x_coords = np.array([pos[0] for pos in disc_positions])
        y_coords = np.array([pos[1] for pos in disc_positions])
        
        # Auto-detect release frame if not provided
        if release_frame_idx is None:
            # Look for frame with maximum velocity
            velocities = []
            for i in range(1, len(frames)):
                dt = (frames[i] - frames[i-1]) / fps
                dx = x_coords[i] - x_coords[i-1]
                dy = y_coords[i] - y_coords[i-1]
                velocity = np.sqrt(dx**2 + dy**2) / dt
                velocities.append((i, velocity))
            
            # Release is typically around maximum velocity
            release_idx = max(velocities, key=lambda v: v[1])[0]
        else:
            # Find the closest frame index to the provided release frame
            release_idx = np.argmin(np.abs(frames - release_frame_idx))
        
        # Use frames after release for speed calculation
        post_release_idx = min(release_idx + 1, len(frames) - 1)
        
        # Ensure we have enough frames after release
        if post_release_idx >= len(frames) - 2:
            logger.warning("Not enough frames after release for accurate speed calculation")
            post_release_idx = len(frames) - 3
            
        # Calculate speed using 3 frames after release for stability
        positions = []
        for i in range(post_release_idx, min(post_release_idx + 3, len(frames))):
            positions.append((frames[i], x_coords[i], y_coords[i]))
        
        # Calculate speed using linear regression on these points
        if len(positions) < 2:
            logger.warning("Not enough points for speed calculation")
            return None
            
        # Extract time and positions
        times = np.array([(pos[0] - positions[0][0])/fps for pos in positions])
        x_pos = np.array([pos[1] for pos in positions])
        y_pos = np.array([pos[2] for pos in positions])
        
        # Fit linear model to x and y positions over time
        def linear_model(t, v, b):
            return v*t + b
            
        try:
            vx, _ = curve_fit(linear_model, times, x_pos)[0]
            vy, _ = curve_fit(linear_model, times, y_pos)[0]
            
            # Calculate total velocity
            velocity_pixels_per_sec = np.sqrt(vx**2 + vy**2)
            
            # Apply calibration if available
            if self.calibration_factor:
                velocity_m_s = velocity_pixels_per_sec / self.calibration_factor
            else:
                # Provide approximate values assuming typical video scale
                velocity_m_s = velocity_pixels_per_sec / 100  # rough estimate
                logger.warning("Using rough estimation due to lack of calibration")
            
            # Convert to other units
            velocity_km_h = velocity_m_s * 3.6
            velocity_mph = velocity_m_s * 2.23694
            
            return {
                "meters_per_second": velocity_m_s,
                "kilometers_per_hour": velocity_km_h,
                "miles_per_hour": velocity_mph,
                "release_frame": frames[release_idx]
            }
            
        except Exception as e:
            logger.error(f"Error calculating speed: {e}")
            return None
    
    def track_disc(self, video_path, start_frame=0, end_frame=None, release_frame=None):
        """
        Track the disc in a video and calculate its release speed.
        
        Args:
            video_path: Path to the video file
            start_frame: First frame to analyze
            end_frame: Last frame to analyze (None for all frames)
            release_frame: Approximate release frame if known
            
        Returns:
            Dictionary with speed metrics and disc positions
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video file: {video_path}")
            return None
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        if end_frame is None:
            end_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Setup background subtractor
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=20, varThreshold=16)
        
        # Initialize variables
        disc_positions = []
        has_calibrated = False
        frame_idx = 0
        
        # Process video frames
        while cap.isOpened() and frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_idx < start_frame:
                frame_idx += 1
                continue
            
            # Apply background subtraction
            fg_mask = bg_subtractor.apply(frame)
            
            # Clean up mask with morphological operations
            kernel = np.ones((5, 5), np.uint8)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size and shape to find disc
            disc_contour = None
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 5000:  # Adjust based on your video
                    # Check if it's roughly circular
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        if circularity > 0.6:  # Discs are fairly circular
                            disc_contour = contour
                            break
            
            # If disc found, record position
            if disc_contour is not None:
                M = cv2.moments(disc_contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    disc_positions.append((cx, cy, frame_idx))
                    
                    # Auto-calibrate on first clear detection
                    if not has_calibrated and self.calibration_factor is None:
                        has_calibrated = self.auto_calibrate(frame, disc_contour)
            
            frame_idx += 1
            
            # Log progress
            if frame_idx % 30 == 0:
                logger.info(f"Processed {frame_idx} frames, found {len(disc_positions)} disc positions")
        
        # Calculate speed
        speed_data = self.calculate_release_speed(disc_positions, fps, release_frame)
        
        # Return results
        return {
            "speed": speed_data,
            "disc_positions": disc_positions,
            "calibration_factor": self.calibration_factor,
            "fps": fps
        }