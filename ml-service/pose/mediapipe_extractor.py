"""
MediaPipe-based pose extraction for disc golf video analysis.

Uses MediaPipe Pose to extract skeleton landmarks from video frames,
focusing on key body parts relevant to disc golf throw mechanics.
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PoseLandmark:
    """A single pose landmark with 3D coordinates and visibility."""
    x: float
    y: float
    z: float
    visibility: float


@dataclass
class FramePose:
    """Pose data for a single video frame."""
    frame_number: int
    timestamp_ms: float
    landmarks: Dict[str, PoseLandmark]
    detected: bool


# MediaPipe landmark indices for disc golf analysis
LANDMARK_INDICES = {
    'nose': 0,
    'left_shoulder': 11,
    'right_shoulder': 12,
    'left_elbow': 13,
    'right_elbow': 14,
    'left_wrist': 15,
    'right_wrist': 16,
    'left_hip': 23,
    'right_hip': 24,
    'left_knee': 25,
    'right_knee': 26,
    'left_ankle': 27,
    'right_ankle': 28,
}


class MediaPipePoseExtractor:
    """
    Extracts pose landmarks from video frames using MediaPipe.

    Optimized for disc golf throw analysis with focus on:
    - Shoulder rotation tracking
    - Hip rotation measurement
    - Wrist position for reachback and release
    - Lower body positioning
    """

    def __init__(self, min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 sample_rate: int = 2):
        """
        Initialize the pose extractor.

        Args:
            min_detection_confidence: Minimum confidence for pose detection
            min_tracking_confidence: Minimum confidence for landmark tracking
            sample_rate: Process every Nth frame (1 = all frames)
        """
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.sample_rate = sample_rate

        if not MEDIAPIPE_AVAILABLE:
            logger.warning("MediaPipe not available. Pose extraction will return empty results.")
            self.pose = None
        else:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence
            )

    def extract_poses_from_video(self, video_path: str,
                                  max_frames: int = 300) -> List[FramePose]:
        """
        Extract pose landmarks from all frames in a video.

        Args:
            video_path: Path to the video file
            max_frames: Maximum number of frames to process

        Returns:
            List of FramePose objects with detected landmarks
        """
        if not MEDIAPIPE_AVAILABLE or self.pose is None:
            logger.warning("MediaPipe not available, returning empty pose list")
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        poses = []
        frame_count = 0

        logger.info(f"Extracting poses from video at {fps} fps, sample_rate={self.sample_rate}")

        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            # Only process every Nth frame
            if frame_count % self.sample_rate != 0:
                frame_count += 1
                continue

            timestamp_ms = (frame_count / fps) * 1000
            frame_pose = self._process_frame(frame, frame_count, timestamp_ms)
            poses.append(frame_pose)

            frame_count += 1

        cap.release()

        detected_count = sum(1 for p in poses if p.detected)
        logger.info(f"Extracted {len(poses)} frames, {detected_count} with detected poses")

        return poses

    def _process_frame(self, frame: np.ndarray, frame_number: int,
                       timestamp_ms: float) -> FramePose:
        """Process a single frame and extract pose landmarks."""
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        results = self.pose.process(rgb_frame)

        if results.pose_landmarks is None:
            return FramePose(
                frame_number=frame_number,
                timestamp_ms=timestamp_ms,
                landmarks={},
                detected=False
            )

        # Extract relevant landmarks
        landmarks = {}
        for name, idx in LANDMARK_INDICES.items():
            lm = results.pose_landmarks.landmark[idx]
            landmarks[name] = PoseLandmark(
                x=lm.x,
                y=lm.y,
                z=lm.z,
                visibility=lm.visibility
            )

        return FramePose(
            frame_number=frame_number,
            timestamp_ms=timestamp_ms,
            landmarks=landmarks,
            detected=True
        )

    def get_keyframe_indices(self, poses: List[FramePose]) -> Dict[str, int]:
        """
        Identify key frames in the throwing motion.

        Detects:
        - setup: Initial stable position
        - reachback: Maximum arm extension behind body
        - release: Point of disc release (peak wrist velocity)
        - follow_through: End of throwing motion

        Args:
            poses: List of extracted poses

        Returns:
            Dictionary mapping phase names to frame indices
        """
        if not poses or len(poses) < 5:
            return {}

        keyframes = {}
        detected_poses = [p for p in poses if p.detected]

        if len(detected_poses) < 5:
            return {}

        # Calculate wrist positions over time (assuming right-handed thrower)
        wrist_x = []
        for pose in detected_poses:
            if 'right_wrist' in pose.landmarks:
                wrist_x.append(pose.landmarks['right_wrist'].x)
            else:
                wrist_x.append(0.5)  # Default center

        wrist_x = np.array(wrist_x)

        # Reachback: minimum wrist x (furthest back)
        reachback_idx = int(np.argmin(wrist_x))
        keyframes['reachback'] = detected_poses[reachback_idx].frame_number

        # Setup: first stable frame (before significant movement)
        keyframes['setup'] = detected_poses[0].frame_number

        # Release: maximum wrist velocity (derivative peak after reachback)
        if len(wrist_x) > reachback_idx + 2:
            velocities = np.diff(wrist_x[reachback_idx:])
            release_idx = reachback_idx + int(np.argmax(velocities)) + 1
            release_idx = min(release_idx, len(detected_poses) - 1)
            keyframes['release'] = detected_poses[release_idx].frame_number

        # Follow-through: last detected frame
        keyframes['follow_through'] = detected_poses[-1].frame_number

        return keyframes

    def close(self):
        """Release MediaPipe resources."""
        if self.pose is not None:
            self.pose.close()
