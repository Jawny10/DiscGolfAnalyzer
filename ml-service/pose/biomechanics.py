"""
Biomechanics analysis for disc golf throws.

Calculates key metrics from pose data:
- Reachback depth
- Hip rotation
- Shoulder separation (X-factor)
- Follow-through quality
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from .mediapipe_extractor import FramePose, PoseLandmark

logger = logging.getLogger(__name__)


@dataclass
class BiomechanicsMetrics:
    """Computed biomechanics metrics for a disc golf throw."""
    reachback_depth_score: int = 0  # 0-100
    hip_rotation_degrees: float = 0.0
    shoulder_separation_degrees: float = 0.0
    follow_through_score: int = 0  # 0-100
    weight_shift_score: int = 0  # 0-100

    # Additional detail metrics
    max_reachback_x: float = 0.0
    release_point_x: float = 0.0
    hip_shoulder_timing_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'reachback_depth_score': self.reachback_depth_score,
            'hip_rotation_degrees': round(self.hip_rotation_degrees, 1),
            'shoulder_separation_degrees': round(self.shoulder_separation_degrees, 1),
            'follow_through_score': self.follow_through_score,
            'weight_shift_score': self.weight_shift_score,
        }


class BiomechanicsAnalyzer:
    """
    Analyzes disc golf throwing mechanics from pose sequences.

    Key metrics for disc golf:
    1. Reachback depth - How far back the arm extends
    2. Hip rotation - Degrees of hip turn during throw
    3. Shoulder separation (X-factor) - Angle between hips and shoulders
    4. Follow-through - Arm extension and rotation after release
    """

    def __init__(self, handedness: str = 'right'):
        """
        Initialize the analyzer.

        Args:
            handedness: 'right' or 'left' for throwing hand
        """
        self.handedness = handedness
        self.throwing_wrist = f'{handedness}_wrist'
        self.throwing_elbow = f'{handedness}_elbow'
        self.throwing_shoulder = f'{handedness}_shoulder'

        # Opposite side landmarks
        other = 'left' if handedness == 'right' else 'right'
        self.other_wrist = f'{other}_wrist'
        self.other_shoulder = f'{other}_shoulder'

    def analyze(self, poses: List[FramePose],
                keyframes: Optional[Dict[str, int]] = None) -> BiomechanicsMetrics:
        """
        Analyze a sequence of poses and compute biomechanics metrics.

        Args:
            poses: List of FramePose objects from video analysis
            keyframes: Optional dict of keyframe indices (setup, reachback, release, follow_through)

        Returns:
            BiomechanicsMetrics with computed scores
        """
        if not poses:
            logger.warning("No poses provided for analysis")
            return BiomechanicsMetrics()

        detected_poses = [p for p in poses if p.detected]
        if len(detected_poses) < 3:
            logger.warning(f"Insufficient detected poses: {len(detected_poses)}")
            return BiomechanicsMetrics()

        metrics = BiomechanicsMetrics()

        # Calculate each metric
        metrics.reachback_depth_score = self._calculate_reachback(detected_poses)
        metrics.hip_rotation_degrees = self._calculate_hip_rotation(detected_poses)
        metrics.shoulder_separation_degrees = self._calculate_shoulder_separation(detected_poses)
        metrics.follow_through_score = self._calculate_follow_through(detected_poses)
        metrics.weight_shift_score = self._calculate_weight_shift(detected_poses)

        return metrics

    def _calculate_reachback(self, poses: List[FramePose]) -> int:
        """
        Calculate reachback depth score (0-100).

        Measures how far the wrist extends behind the body during reachback.
        Pro-level reachback typically has the wrist well behind the rear shoulder.
        """
        min_wrist_x = 1.0
        shoulder_x_at_reachback = 0.5

        for pose in poses:
            if self.throwing_wrist not in pose.landmarks:
                continue

            wrist = pose.landmarks[self.throwing_wrist]
            if wrist.x < min_wrist_x:
                min_wrist_x = wrist.x
                if self.throwing_shoulder in pose.landmarks:
                    shoulder_x_at_reachback = pose.landmarks[self.throwing_shoulder].x

        # Reachback depth = how far wrist is behind shoulder
        # Normalized coordinates (0-1), so difference matters
        depth = shoulder_x_at_reachback - min_wrist_x

        # Score: 0-0.1 depth = 0-50, 0.1-0.25 = 50-100
        if depth < 0:
            score = 30  # Wrist never got behind shoulder
        elif depth < 0.1:
            score = int(30 + (depth / 0.1) * 30)
        else:
            score = int(60 + min((depth - 0.1) / 0.15, 1.0) * 40)

        return min(100, max(0, score))

    def _calculate_hip_rotation(self, poses: List[FramePose]) -> float:
        """
        Calculate hip rotation in degrees.

        Measures the angle change of the hip line from setup to release.
        Pro-level throws typically show 40-60 degrees of hip rotation.
        """
        if len(poses) < 2:
            return 0.0

        def get_hip_angle(pose: FramePose) -> Optional[float]:
            if 'left_hip' not in pose.landmarks or 'right_hip' not in pose.landmarks:
                return None
            left = pose.landmarks['left_hip']
            right = pose.landmarks['right_hip']
            return np.degrees(np.arctan2(right.y - left.y, right.x - left.x))

        # Get angles at different phases
        angles = [get_hip_angle(p) for p in poses]
        angles = [a for a in angles if a is not None]

        if len(angles) < 2:
            return 0.0

        # Find the range of rotation
        # Early frames = setup, later frames = through release
        early_angle = np.mean(angles[:len(angles)//4 + 1])
        late_angle = np.mean(angles[len(angles)*3//4:])

        rotation = abs(late_angle - early_angle)
        return min(90.0, rotation)  # Cap at 90 degrees

    def _calculate_shoulder_separation(self, poses: List[FramePose]) -> float:
        """
        Calculate X-factor (shoulder-hip separation angle).

        Measures the maximum angle between the shoulder line and hip line.
        This separation creates torque for power generation.
        Pro-level throws often show 30-50 degrees of separation.
        """
        max_separation = 0.0

        for pose in poses:
            hip_angle = self._get_line_angle(pose, 'left_hip', 'right_hip')
            shoulder_angle = self._get_line_angle(pose, 'left_shoulder', 'right_shoulder')

            if hip_angle is not None and shoulder_angle is not None:
                separation = abs(shoulder_angle - hip_angle)
                # Normalize to 0-90 range
                if separation > 90:
                    separation = 180 - separation
                max_separation = max(max_separation, separation)

        return max_separation

    def _calculate_follow_through(self, poses: List[FramePose]) -> int:
        """
        Calculate follow-through quality score (0-100).

        Measures arm extension and rotation after the release point.
        Good follow-through shows the arm continuing across the body.
        """
        if len(poses) < 3:
            return 50

        # Use the last third of poses as follow-through
        follow_poses = poses[len(poses)*2//3:]

        max_wrist_x = 0.0
        max_extension = 0.0

        for pose in follow_poses:
            if self.throwing_wrist not in pose.landmarks:
                continue

            wrist = pose.landmarks[self.throwing_wrist]
            max_wrist_x = max(max_wrist_x, wrist.x)

            # Check arm extension (wrist relative to shoulder)
            if self.throwing_shoulder in pose.landmarks:
                shoulder = pose.landmarks[self.throwing_shoulder]
                extension = abs(wrist.x - shoulder.x)
                max_extension = max(max_extension, extension)

        # Score based on how far wrist travels across body
        # and how extended the arm gets
        wrist_score = min(50, max_wrist_x * 60)
        extension_score = min(50, max_extension * 150)

        return int(wrist_score + extension_score)

    def _calculate_weight_shift(self, poses: List[FramePose]) -> int:
        """
        Calculate weight shift score (0-100).

        Measures movement of hips from back foot to front foot.
        Pro-level throws show decisive weight transfer.
        """
        if len(poses) < 2:
            return 50

        hip_centers = []
        for pose in poses:
            if 'left_hip' in pose.landmarks and 'right_hip' in pose.landmarks:
                left = pose.landmarks['left_hip']
                right = pose.landmarks['right_hip']
                center_x = (left.x + right.x) / 2
                hip_centers.append(center_x)

        if len(hip_centers) < 2:
            return 50

        # Weight shift = movement of hip center
        total_shift = hip_centers[-1] - hip_centers[0]

        # Positive shift (moving forward) is good for RHBH
        if self.handedness == 'right':
            shift_quality = total_shift
        else:
            shift_quality = -total_shift

        # Score: shift of 0.05-0.15 normalized coords is good
        if shift_quality < 0:
            score = 30  # Backward weight shift
        elif shift_quality < 0.05:
            score = int(30 + (shift_quality / 0.05) * 20)
        else:
            score = int(50 + min((shift_quality - 0.05) / 0.1, 1.0) * 50)

        return min(100, max(0, score))

    def _get_line_angle(self, pose: FramePose, landmark1: str, landmark2: str) -> Optional[float]:
        """Calculate angle of line between two landmarks."""
        if landmark1 not in pose.landmarks or landmark2 not in pose.landmarks:
            return None

        p1 = pose.landmarks[landmark1]
        p2 = pose.landmarks[landmark2]

        return np.degrees(np.arctan2(p2.y - p1.y, p2.x - p1.x))
