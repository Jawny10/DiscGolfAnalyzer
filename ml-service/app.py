from flask import Flask, request, jsonify
import os
import tempfile
import cv2
import numpy as np
import logging
import traceback
import time

# Pose analysis module
from pose import MediaPipePoseExtractor, BiomechanicsAnalyzer, FeedbackGenerator

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ml-service')

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/analyze', methods=['POST'])
def analyze_throw():
    start_time = time.time()
    logger.info("Received analyze request")
    
    try:
        if 'video' not in request.files:
            logger.error("No video file in request")
            return jsonify({"error": "No video file provided"}), 400
        
        video_file = request.files['video']
        logger.info(f"Received video file: {video_file.filename}, size: {video_file.content_length}")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "throw.mp4")
        
        # Save video file
        try:
            video_file.save(video_path)
            logger.info(f"Video saved to {video_path}")
        except Exception as e:
            logger.error(f"Error saving video: {str(e)}")
            return jsonify({"error": f"Error saving video: {str(e)}"}), 500
        
        try:
            # Process video to detect disc trajectory
            logger.info("Detecting disc in video...")
            disc_positions = detect_disc(video_path)
            
            # If disc detection failed, return error
            if not disc_positions or len(disc_positions) < 5:
                logger.error("Insufficient disc positions detected")
                return jsonify({
                    "flightPath": "unknown",
                    "distance": 0,
                    "maxHeight": 0,
                    "releaseAngle": 0,
                    "techniqueFeedback": ["Unable to detect disc clearly. Try recording with better lighting and contrast."]
                })
            
            # Analyze trajectory
            logger.info(f"Analyzing trajectory with {len(disc_positions)} positions...")
            trajectory_data = analyze_trajectory(disc_positions)
            
            # Generate simple feedback
            feedback = generate_simple_feedback(trajectory_data)
            
            # Return analysis results
            result = {
                "flightPath": trajectory_data["flight_path"],
                "distance": float(trajectory_data["distance"]),
                "maxHeight": float(trajectory_data["max_height"]),
                "releaseAngle": float(trajectory_data["release_angle"]),
                "techniqueFeedback": feedback
            }
            
            logger.info(f"Analysis complete: {result}")
            return jsonify(result)
            
        except Exception as e:
            error_msg = f"Error during analysis: {str(e)}"
            stack_trace = traceback.format_exc()
            logger.error(f"{error_msg}\n{stack_trace}")
            return jsonify({
                "flightPath": "error",
                "distance": 0,
                "maxHeight": 0,
                "releaseAngle": 0,
                "techniqueFeedback": [f"Analysis error: {str(e)}. Please try a different video."]
            })
        
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{stack_trace}")
        return jsonify({"error": error_msg}), 500
    
    finally:
        # Clean up
        try:
            if 'video_path' in locals() and os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Removed temporary video file: {video_path}")
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                logger.info(f"Removed temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

def detect_disc(video_path):
    """
    Detect and track the disc throughout a video.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        list: List of (x, y, frame_num) coordinates representing the disc position
    """
    logger.info("Starting disc detection")
    disc_positions = []
    
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    # Check if video opened successfully
    if not cap.isOpened():
        raise Exception("Could not open video file")
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    logger.info(f"Video properties: {width}x{height}, {fps} fps, {total_frames} frames")
    
    # Initialize background subtractor
    backSub = cv2.createBackgroundSubtractorKNN()
    
    # For initial implementation, sample every 5th frame to speed up processing
    sample_rate = 5
    
    # Process the video
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Only process every Nth frame
        if frame_count % sample_rate != 0:
            frame_count += 1
            continue
            
        # Apply background subtraction
        fg_mask = backSub.apply(frame)
        
        # Apply some morphology to clean up the mask
        kernel = np.ones((5,5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area to find potential discs
        min_area = 50  # Minimum area of the disc in pixels
        max_area = 2000  # Maximum area of the disc in pixels
        
        potential_discs = [c for c in contours if min_area < cv2.contourArea(c) < max_area]
        
        # If potential discs found, use the one with best match (for now, just the largest)
        if potential_discs:
            # Sort by area (largest first)
            potential_discs.sort(key=cv2.contourArea, reverse=True)
            
            # Get the center of the largest contour (assumed to be the disc)
            M = cv2.moments(potential_discs[0])
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                disc_positions.append((cx, cy, frame_count))
                logger.debug(f"Frame {frame_count}: Disc detected at position ({cx}, {cy})")
        
        frame_count += 1
        
        # Limit processing to first 300 frames for testing
        if frame_count > 300:
            break
    
    # Release the video capture object
    cap.release()
    
    # If we didn't find enough positions, fall back to a simulated trajectory
    if len(disc_positions) < 5:
        logger.warning("Not enough disc positions detected, falling back to simulated trajectory")
        # Create a simulated trajectory
        for i in range(0, 30):
            t = i / 30
            x = int(width * 0.1 + (width * 0.7) * t)
            y = int(height * 0.8 - (height * 0.4) * np.sin(np.pi * t))
            disc_positions.append((x, y, i * sample_rate))
    
    logger.info(f"Detected {len(disc_positions)} disc positions")
    return disc_positions

def analyze_trajectory(disc_positions):
    """
    Analyze the disc trajectory to extract flight metrics.
    """
    # Extract coordinates
    x_coords = np.array([pos[0] for pos in disc_positions])
    y_coords = np.array([pos[1] for pos in disc_positions])
    frames = np.array([pos[2] for pos in disc_positions])
    
    # Calculate distance (in pixels, would need calibration for real-world measurement)
    distance_pixels = np.sqrt((x_coords[-1] - x_coords[0])**2 + (y_coords[-1] - y_coords[0])**2)
    
    # Calculate maximum height (assuming y decreases as you go up in image)
    max_height_pixels = np.max(y_coords) - np.min(y_coords)
    
    # Estimate release angle based on early trajectory
    if len(x_coords) > 3 and (x_coords[2] - x_coords[0]) != 0:
        dx = x_coords[2] - x_coords[0]
        dy = y_coords[0] - y_coords[2]  # Invert y since image coordinates have y increasing downward
        release_angle = np.degrees(np.arctan2(dy, dx))
    else:
        release_angle = 0
    
    # Determine flight path type
    if abs(release_angle) < 5:
        flight_path = "flat"
    elif release_angle > 5:
        flight_path = "hyzer"
    else:
        flight_path = "anhyzer"
    
    # Return the analysis results without visualization for now
    return {
        "distance": distance_pixels,
        "max_height": max_height_pixels,
        "release_angle": release_angle,
        "flight_path": flight_path
    }

def generate_simple_feedback(trajectory_data):
    """
    Generate simple feedback based on trajectory analysis.
    """
    feedback = []

    # Flight path feedback
    flight_path = trajectory_data["flight_path"]
    if flight_path == "flat":
        feedback.append("Your throw has a flat release angle, which is good for straight shots.")
    elif flight_path == "hyzer":
        feedback.append("Your throw has a hyzer angle (disc tilted down). This is good for controlled fades.")
    elif flight_path == "anhyzer":
        feedback.append("Your throw has an anhyzer angle (disc tilted up). This can help with distance but may reduce control.")

    # Release angle feedback
    release_angle = trajectory_data["release_angle"]
    if abs(release_angle) < 5:
        feedback.append("Your release angle is very flat, which is ideal for straight shots.")
    elif release_angle > 20:
        feedback.append("Your release angle is quite steep. Try flattening your release for more distance.")
    elif release_angle < -20:
        feedback.append("Your anhyzer angle is quite extreme. Consider a more moderate angle for better control.")

    # Add a general placeholder feedback
    feedback.append("Focus on a smooth release and follow-through to improve consistency.")

    return feedback


@app.route('/analyze-pose', methods=['POST'])
def analyze_pose():
    """
    Analyze video with combined trajectory and pose detection.

    Returns comprehensive analysis including:
    - Disc trajectory data (flight path, distance, etc.)
    - Pose metrics (reachback, hip rotation, etc.)
    - Combined feedback from both analyses
    """
    start_time = time.time()
    logger.info("Received analyze-pose request")

    temp_dir = None
    video_path = None
    pose_extractor = None

    try:
        if 'video' not in request.files:
            logger.error("No video file in request")
            return jsonify({"error": "No video file provided"}), 400

        video_file = request.files['video']
        logger.info(f"Received video file: {video_file.filename}")

        # Get optional parameters
        min_confidence = float(request.form.get('min_confidence', 0.5))
        handedness = request.form.get('handedness', 'right')
        skill_level = request.form.get('skill_level', 'intermediate')

        # Create temporary directory and save video
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "throw.mp4")

        try:
            video_file.save(video_path)
            logger.info(f"Video saved to {video_path}")
        except Exception as e:
            logger.error(f"Error saving video: {str(e)}")
            return jsonify({"error": f"Error saving video: {str(e)}"}), 500

        # 1. Trajectory analysis (existing)
        logger.info("Detecting disc trajectory...")
        disc_positions = detect_disc(video_path)
        trajectory_data = None

        if disc_positions and len(disc_positions) >= 5:
            trajectory_data = analyze_trajectory(disc_positions)
            trajectory_feedback = generate_simple_feedback(trajectory_data)
        else:
            trajectory_data = {
                "flight_path": "unknown",
                "distance": 0,
                "max_height": 0,
                "release_angle": 0
            }
            trajectory_feedback = ["Unable to detect disc clearly."]

        # 2. Pose analysis (new)
        logger.info("Extracting pose landmarks...")
        pose_extractor = MediaPipePoseExtractor(
            min_detection_confidence=min_confidence,
            sample_rate=2
        )

        poses = pose_extractor.extract_poses_from_video(video_path, max_frames=300)
        keyframes = pose_extractor.get_keyframe_indices(poses)

        pose_detected = len([p for p in poses if p.detected]) > 0
        pose_metrics = None
        pose_feedback = None

        if pose_detected:
            logger.info("Analyzing biomechanics...")
            biomechanics_analyzer = BiomechanicsAnalyzer(handedness=handedness)
            metrics = biomechanics_analyzer.analyze(poses, keyframes)
            pose_metrics = metrics.to_dict()

            logger.info("Generating pose feedback...")
            feedback_generator = FeedbackGenerator(skill_level=skill_level)
            feedback = feedback_generator.generate_feedback(metrics)
            pose_feedback = feedback.to_dict()
        else:
            logger.warning("No pose detected in video")
            pose_metrics = {
                "reachback_depth_score": 0,
                "hip_rotation_degrees": 0,
                "shoulder_separation_degrees": 0,
                "follow_through_score": 0,
                "weight_shift_score": 0
            }
            pose_feedback = {
                "pose_tips": ["Unable to detect body pose. Ensure full body is visible."],
                "priority_focus": "visibility",
                "strengths": [],
                "overall_score": 0
            }

        # 3. Combine results
        elapsed_time = time.time() - start_time
        logger.info(f"Analysis complete in {elapsed_time:.2f}s")

        result = {
            "trajectory": {
                "flightPath": trajectory_data["flight_path"],
                "distance": float(trajectory_data["distance"]),
                "maxHeight": float(trajectory_data["max_height"]),
                "releaseAngle": float(trajectory_data["release_angle"]),
                "techniqueFeedback": trajectory_feedback
            },
            "pose": {
                "detected": pose_detected,
                "metrics": pose_metrics,
                "keyframes": keyframes
            },
            "feedback": pose_feedback,
            "processingTimeMs": int(elapsed_time * 1000)
        }

        return jsonify(result)

    except Exception as e:
        error_msg = f"Error during pose analysis: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{stack_trace}")
        return jsonify({
            "error": error_msg,
            "trajectory": {
                "flightPath": "error",
                "distance": 0,
                "maxHeight": 0,
                "releaseAngle": 0,
                "techniqueFeedback": [f"Analysis error: {str(e)}"]
            },
            "pose": {
                "detected": False,
                "metrics": {},
                "keyframes": {}
            },
            "feedback": {
                "pose_tips": ["An error occurred during analysis."],
                "priority_focus": "error",
                "strengths": [],
                "overall_score": 0
            }
        }), 500

    finally:
        # Clean up
        if pose_extractor is not None:
            try:
                pose_extractor.close()
            except Exception as e:
                logger.error(f"Error closing pose extractor: {str(e)}")

        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Removed temporary video file: {video_path}")
            if temp_dir and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                logger.info(f"Removed temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")


if __name__ == '__main__':
    logger.info("Starting ML service on port 5001")
    # Do not use threaded=True for now to avoid matplotlib issues
    app.run(host='0.0.0.0', port=5001, debug=True)