# ml-service/analysis/technique.py

import numpy as np
from scipy.signal import savgol_filter

def analyze_technique(disc_positions, trajectory_data):
    """
    Analyze throwing technique based on disc trajectory.
    
    Args:
        disc_positions (list): List of (x, y, frame_num) coordinates
        trajectory_data (dict): Dictionary containing flight metrics
        
    Returns:
        dict: Dictionary containing technique analysis
    """
    if not disc_positions or len(disc_positions) < 5:
        return {"error": "Insufficient data for technique analysis"}
    
    # Extract coordinates and convert to numpy arrays
    x_coords = np.array([pos[0] for pos in disc_positions])
    y_coords = np.array([pos[1] for pos in disc_positions])
    
    # Calculate velocity at each point
    x_vel = np.diff(x_coords)
    y_vel = np.diff(y_coords)
    velocities = np.sqrt(x_vel**2 + y_vel**2)
    
    # Smooth the velocity curve
    if len(velocities) > 5:
        try:
            velocities_smooth = savgol_filter(velocities, min(5, len(velocities) // 2 * 2 + 1), 2)
        except Exception:
            velocities_smooth = velocities
    else:
        velocities_smooth = velocities
    
    # Find the release point (assume it's where velocity is highest)
    if len(velocities_smooth) > 0:
        release_idx = np.argmax(velocities_smooth)
    else:
        release_idx = 0
    
    # Analyze release angle
    if release_idx < len(x_vel) and release_idx < len(y_vel):
        release_angle = np.degrees(np.arctan2(-y_vel[release_idx], x_vel[release_idx]))
    else:
        release_angle = 0
    
    # Calculate consistency of the throw (lower variation = more consistent)
    if len(velocities) > 1:
        consistency = 1.0 - min(1.0, np.std(velocities) / np.mean(velocities))
    else:
        consistency = 0
    
    # Analyze flight stability
    flight_path = trajectory_data.get("flight_path", "undetermined")
    
    # Check if the throw has wobble (variations in y direction)
    if len(y_coords) > 5:
        # Fit a trend line to y coordinates
        x_indices = np.arange(len(y_coords))
        coeffs = np.polyfit(x_indices, y_coords, 2)
        y_trend = np.polyval(coeffs, x_indices)
        
        # Calculate residuals (deviations from the trend)
        residuals = y_coords - y_trend
        wobble = np.std(residuals)
    else:
        wobble = 0
    
    return {
        "release_angle": float(release_angle),
        "consistency": float(consistency),
        "wobble": float(wobble),
        "flight_path": flight_path
    }