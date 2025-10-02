# ml-service/test_video_processor.py

import cv2
import numpy as np
import os
from video_processor.disc_detection import detect_disc
from video_processor.trajectory import analyze_trajectory
from analysis.technique import analyze_technique
from analysis.feedback import generate_feedback

def create_test_video():
    """Create a simple test video with a moving object"""
    # Define video parameters
    width, height = 640, 480
    fps = 30
    seconds = 3
    
    # Create a test video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('test_video.mp4', fourcc, fps, (width, height))
    
    # Create a moving "disc" (white circle)
    for i in range(fps * seconds):
        # Create a black frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Calculate position for a simple parabolic trajectory
        t = i / fps
        x = int(width * 0.2 + (width * 0.6) * (t / seconds))
        y = int(height * 0.8 - (height * 0.5) * np.sin(np.pi * t / seconds))
        
        # Draw a white circle to represent the disc
        cv2.circle(frame, (x, y), 15, (255, 255, 255), -1)
        
        # Write the frame
        out.write(frame)
    
    out.release()
    print("Test video created: test_video.mp4")
    
    # Return the expected trajectory points for testing
    points = []
    for i in range(fps * seconds):
        t = i / fps
        x = int(width * 0.2 + (width * 0.6) * (t / seconds))
        y = int(height * 0.8 - (height * 0.5) * np.sin(np.pi * t / seconds))
        points.append((x, y, i))
    
    return points

def test_pipeline():
    """Test the entire video processing pipeline"""
    # Create a test video
    expected_points = create_test_video()
    
    if not os.path.exists('test_video.mp4'):
        print("Failed to create test video!")
        return
    
    print("Testing disc detection...")
    try:
        # Detect disc in the video
        disc_positions = detect_disc('test_video.mp4')
        print(f"Detected {len(disc_positions)} disc positions")
        
        # Compare with expected (just check if we have a reasonable number of points)
        if len(disc_positions) > len(expected_points) * 0.5:
            print("✓ Disc detection working")
        else:
            print("✗ Disc detection not capturing enough points")
    except Exception as e:
        print(f"✗ Disc detection failed: {e}")
        return
    
    print("\nTesting trajectory analysis...")
    try:
        # Analyze trajectory
        trajectory_data = analyze_trajectory(disc_positions)
        print("Trajectory data:")
        for key, value in trajectory_data.items():
            print(f"  {key}: {value}")
        print("✓ Trajectory analysis working")
    except Exception as e:
        print(f"✗ Trajectory analysis failed: {e}")
        return
    
    print("\nTesting technique analysis...")
    try:
        # Analyze technique
        technique_data = analyze_technique(disc_positions, trajectory_data)
        print("Technique data:")
        for key, value in technique_data.items():
            print(f"  {key}: {value}")
        print("✓ Technique analysis working")
    except Exception as e:
        print(f"✗ Technique analysis failed: {e}")
        return
    
    print("\nTesting feedback generation...")
    try:
        # Generate feedback
        feedback = generate_feedback(technique_data)
        print("Feedback:")
        for item in feedback:
            print(f"  • {item}")
        print("✓ Feedback generation working")
    except Exception as e:
        print(f"✗ Feedback generation failed: {e}")
        return
    
    print("\n✓ Complete pipeline test successful!")

if __name__ == "__main__":
    test_pipeline()