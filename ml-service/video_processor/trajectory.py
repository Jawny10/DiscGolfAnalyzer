# ml-service/video_processor/trajectory.py

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os

def analyze_trajectory(disc_positions):
    """
    Analyze disc trajectory to extract flight metrics.
    
    Args:
        disc_positions (list): List of (x, y, frame_num) coordinates
        
    Returns:
        dict: Dictionary containing flight metrics
    """
    if not disc_positions or len(disc_positions) < 3:
        raise Exception("Insufficient disc positions detected for analysis")
    
    # Extract coordinates
    x_coords = np.array([pos[0] for pos in disc_positions])
    y_coords = np.array([pos[1] for pos in disc_positions])
    frames = np.array([pos[2] for pos in disc_positions])
    
    # Calculate distance (in pixels, would need calibration for real-world measurement)
    distance_pixels = np.sqrt((x_coords[-1] - x_coords[0])**2 + (y_coords[-1] - y_coords[0])**2)
    
    # Calculate height (assuming y decreases as you go up in image)
    max_height_pixels = np.max(y_coords) - np.min(y_coords)
    
    # Determine flight path type based on trajectory
    # Fit a quadratic curve to the trajectory
    def quadratic_func(x, a, b, c):
        return a * (x**2) + b * x + c
    
    try:
        # Fit curve
        params, _ = curve_fit(quadratic_func, x_coords, y_coords)
        a, b, c = params
        
        # Generate fitted curve
        x_fit = np.linspace(np.min(x_coords), np.max(x_coords), 100)
        y_fit = quadratic_func(x_fit, a, b, c)
        
        # Create a visualization of the trajectory
        plt.figure(figsize=(10, 6))
        plt.scatter(x_coords, y_coords, color='blue', label='Disc positions')
        plt.plot(x_fit, y_fit, 'r-', label='Fitted trajectory')
        plt.xlabel('X position (pixels)')
        plt.ylabel('Y position (pixels)')
        plt.title('Disc Flight Trajectory')
        plt.legend()
        plt.grid(True)
        
        # Save the trajectory visualization
        os.makedirs('output', exist_ok=True)
        trajectory_image_path = 'output/trajectory.png'
        plt.savefig(trajectory_image_path)
        plt.close()
        
        # Determine flight path type based on curve parameters
        if abs(a) < 0.001:  # Almost straight
            flight_path = "straight"
        elif a > 0:  # Curves right for RHBH throw (assuming x increases to the right)
            flight_path = "hyzer"
        else:  # Curves left for RHBH throw
            flight_path = "anhyzer"
            
    except Exception as e:
        print(f"Error fitting trajectory: {e}")
        flight_path = "undetermined"
        trajectory_image_path = None
    
    # Calculate initial velocity (simplified)
    if len(frames) > 1:
        dx = x_coords[1] - x_coords[0]
        dy = y_coords[1] - y_coords[0]
        dt = frames[1] - frames[0]  # Assuming constant frame rate
        initial_velocity = np.sqrt(dx**2 + dy**2) / dt
    else:
        initial_velocity = 0
    
    return {
        "distance": float(distance_pixels),
        "max_height": float(max_height_pixels),
        "flight_path": flight_path,
        "initial_velocity": float(initial_velocity),
        "trajectory_image": trajectory_image_path
    }