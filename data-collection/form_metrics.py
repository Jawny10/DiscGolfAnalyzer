# form_metrics.py
import numpy as np
import logging
import json
from scipy.signal import savgol_filter

logger = logging.getLogger(__name__)

def calculate_angle(a, b, c):
    """Calculate the angle between three points in degrees"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    ba = a - b
    bc = c - b
    
    # Handle potential numerical instability
    cosine_angle = np.clip(np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc)), -1.0, 1.0)
    angle = np.arccos(cosine_angle)
    
    return np.degrees(angle)

def get_landmark_coord(landmarks, name):
    """Get coordinates for a specific landmark by name"""
    for lm in landmarks:
        if lm['name'] == name:
            return [lm['x'], lm['y'], lm['z']]
    return None

def smooth_angles(angles, window_length=11, poly_order=3):
    """Apply Savitzky-Golay filter to smooth angle data"""
    if len(angles) < window_length:
        return angles
    
    # Ensure window_length is odd
    if window_length % 2 == 0:
        window_length += 1
    
    # Apply smoothing
    try:
        smoothed = savgol_filter(angles, window_length, poly_order)
        return smoothed
    except Exception as e:
        logger.warning(f"Smoothing failed: {e}. Returning original data.")
        return angles

def unwrap_angles(angles):
    """Unwrap angle measurements to handle discontinuities (e.g., -180° to 180° jumps)"""
    return np.unwrap(np.array(angles) * np.pi/180) * 180/np.pi

def calculate_metrics(poses):
    """Calculate form metrics from pose sequence"""
    logger.info(f"Calculating metrics from {len(poses)} poses")
    
    raw_metrics = {
        'shoulder_rotation': [],
        'elbow_angle': [],
        'wrist_angle': [],
        'hip_rotation': [],
        'reach_back_extension': [],
        'follow_through_extension': []
    }
    
    # First pass: extract raw measurements from each pose
    frame_numbers = []
    for pose_data in poses:
        frame = pose_data['frame']
        frame_numbers.append(frame)
        landmarks = pose_data['landmarks']
        
        # Calculate shoulder rotation (angle between shoulders relative to horizontal)
        left_shoulder = get_landmark_coord(landmarks, 'LEFT_SHOULDER')
        right_shoulder = get_landmark_coord(landmarks, 'RIGHT_SHOULDER')
        if left_shoulder and right_shoulder:
            # Calculate angle in degrees
            shoulder_angle = np.degrees(np.arctan2(
                right_shoulder[1] - left_shoulder[1], 
                right_shoulder[0] - left_shoulder[0]
            ))
            raw_metrics['shoulder_rotation'].append((frame, shoulder_angle))
        
        # Calculate elbow angle
        shoulder = get_landmark_coord(landmarks, 'RIGHT_SHOULDER')
        elbow = get_landmark_coord(landmarks, 'RIGHT_ELBOW')
        wrist = get_landmark_coord(landmarks, 'RIGHT_WRIST')
        if shoulder and elbow and wrist:
            elbow_angle = calculate_angle(shoulder, elbow, wrist)
            raw_metrics['elbow_angle'].append((frame, elbow_angle))
        
        # Calculate wrist angle
        elbow = get_landmark_coord(landmarks, 'RIGHT_ELBOW')
        wrist = get_landmark_coord(landmarks, 'RIGHT_WRIST')
        index = get_landmark_coord(landmarks, 'RIGHT_INDEX')
        if elbow and wrist and index:
            wrist_angle = calculate_angle(elbow, wrist, index)
            raw_metrics['wrist_angle'].append((frame, wrist_angle))
        
        # Calculate hip rotation
        left_hip = get_landmark_coord(landmarks, 'LEFT_HIP')
        right_hip = get_landmark_coord(landmarks, 'RIGHT_HIP')
        if left_hip and right_hip:
            hip_angle = np.degrees(np.arctan2(
                right_hip[1] - left_hip[1], 
                right_hip[0] - left_hip[0]
            ))
            raw_metrics['hip_rotation'].append((frame, hip_angle))
        
        # Calculate reach back extension (distance from right shoulder to right wrist)
        shoulder = get_landmark_coord(landmarks, 'RIGHT_SHOULDER')
        wrist = get_landmark_coord(landmarks, 'RIGHT_WRIST')
        if shoulder and wrist:
            extension = np.linalg.norm(np.array(shoulder) - np.array(wrist))
            raw_metrics['reach_back_extension'].append((frame, extension))
        
        # Calculate follow through extension (horizontal distance past shoulder)
        shoulder = get_landmark_coord(landmarks, 'RIGHT_SHOULDER') 
        wrist = get_landmark_coord(landmarks, 'RIGHT_WRIST')
        if shoulder and wrist:
            # Positive when wrist is in front of shoulder (follow through)
            horizontal_extension = wrist[0] - shoulder[0]
            raw_metrics['follow_through_extension'].append((frame, horizontal_extension))
    
    # Second pass: apply smoothing and organize the data
    processed_metrics = {}
    
    for metric_name, values in raw_metrics.items():
        if not values:
            continue
            
        frames, measurements = zip(*values)
        
        # Handle discontinuities in angles
        if metric_name in ['shoulder_rotation', 'hip_rotation']:
            measurements = unwrap_angles(measurements)
        
        # Apply smoothing
        measurements_smooth = smooth_angles(measurements)
        
        # Store processed metrics
        processed_metrics[metric_name] = [
            {'frame': frame, 'value': value} 
            for frame, value in zip(frames, measurements_smooth)
        ]
    
    # Identify key moments in the throw based on metrics
    processed_metrics['key_moments'] = identify_key_moments(processed_metrics)
    
    return processed_metrics

def identify_key_moments(metrics):
    """Identify key moments in the throw (reach back, pull through, release, etc.)"""
    key_moments = {}
    
    # Extract reach back point (minimum elbow angle or maximum shoulder rotation)
    if 'elbow_angle' in metrics and metrics['elbow_angle']:
        elbow_angles = [(m['frame'], m['value']) for m in metrics['elbow_angle']]
        frames, angles = zip(*elbow_angles)
        min_angle_idx = np.argmin(angles)
        key_moments['reach_back'] = {
            'frame': frames[min_angle_idx],
            'elbow_angle': angles[min_angle_idx]
        }
    
    # Extract release point (based on extension and elbow angle changes)
    if ('elbow_angle' in metrics and metrics['elbow_angle'] and 
        'reach_back_extension' in metrics and metrics['reach_back_extension']):
        
        # Get frame range after reach back
        reach_back_frame = key_moments.get('reach_back', {}).get('frame', 0)
        
        # Find maximum acceleration of elbow extension after reach back
        elbow_data = sorted([(m['frame'], m['value']) for m in metrics['elbow_angle'] 
                    if m['frame'] > reach_back_frame])
        
        if len(elbow_data) > 10:  # Need enough points for this analysis
            frames, angles = zip(*elbow_data)
            # Calculate rate of change
            angle_diffs = np.diff(angles)
            angle_accel = np.diff(angle_diffs)
            
            if len(angle_accel) > 0:
                max_accel_idx = np.argmax(np.abs(angle_accel))
                if max_accel_idx < len(frames) - 2:  # Ensure we don't go out of bounds
                    key_moments['release'] = {
                        'frame': frames[max_accel_idx + 1],  # +1 because of the diff
                        'elbow_angle': angles[max_accel_idx + 1]
                    }
    
    return key_moments