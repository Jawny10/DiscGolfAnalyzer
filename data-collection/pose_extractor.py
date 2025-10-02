# pose_extractor.py
import cv2
import mediapipe as mp
import numpy as np
import logging
import json

logger = logging.getLogger(__name__)

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def extract_poses(video_path):
    """Extract pose landmarks from a video of a disc golf throw"""
    logger.info(f"Extracting poses from {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video file: {video_path}")
        return None
        
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    logger.info(f"Video properties: {frame_count} frames at {fps} FPS")
    
    # Initialize MediaPipe Pose
    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,
        enable_segmentation=False,
        min_detection_confidence=0.5) as pose:
        
        poses = []
        frame_idx = 0
        
        # Process video frames
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            # Process every other frame for efficiency
            if frame_idx % 2 == 0:
                # Convert to RGB for MediaPipe
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(frame_rgb)
                
                if results.pose_landmarks:
                    # Extract landmarks
                    frame_landmarks = []
                    for idx, landmark in enumerate(results.pose_landmarks.landmark):
                        frame_landmarks.append({
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z,
                            'visibility': landmark.visibility,
                            'name': mp_pose.PoseLandmark(idx).name
                        })
                    
                    poses.append({
                        'frame': frame_idx,
                        'timestamp': frame_idx / fps,
                        'landmarks': frame_landmarks
                    })
            
            frame_idx += 1
            
            # Progress logging
            if frame_idx % 30 == 0:
                logger.info(f"Processed {frame_idx}/{frame_count} frames")
        
        cap.release()
        logger.info(f"Extracted poses from {len(poses)} frames")
        
        return poses