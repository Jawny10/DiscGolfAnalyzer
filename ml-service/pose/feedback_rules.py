"""
Rule-based feedback generation for disc golf throws.

Converts biomechanics metrics into actionable coaching feedback.
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .biomechanics import BiomechanicsMetrics

logger = logging.getLogger(__name__)


@dataclass
class PoseFeedback:
    """Structured feedback from pose analysis."""
    pose_tips: List[str]
    priority_focus: str
    strengths: List[str]
    overall_score: int  # 0-100

    def to_dict(self) -> Dict:
        return {
            'pose_tips': self.pose_tips,
            'priority_focus': self.priority_focus,
            'strengths': self.strengths,
            'overall_score': self.overall_score,
        }


# Feedback rules: (metric_name, threshold_low, threshold_high, feedback_if_low, feedback_if_good)
FEEDBACK_RULES = [
    # Reachback
    ('reachback_depth_score', 50, 75,
     "Extend your reachback further - try to get your throwing hand behind your rear shoulder.",
     "Good reachback extension - you're creating space for acceleration."),

    # Hip rotation
    ('hip_rotation_degrees', 30, 45,
     "Rotate your hips more during the throw. Lead with your hips, not your arm.",
     "Good hip rotation - you're generating power from your lower body."),

    # X-factor (shoulder separation)
    ('shoulder_separation_degrees', 25, 40,
     "Create more separation between your shoulders and hips. Keep shoulders closed longer.",
     "Good shoulder-hip separation - you're building torque effectively."),

    # Follow-through
    ('follow_through_score', 50, 75,
     "Follow through more completely. Let your arm continue across your body after release.",
     "Good follow-through - you're completing the throwing motion."),

    # Weight shift
    ('weight_shift_score', 50, 75,
     "Shift your weight more decisively from back foot to front foot during the throw.",
     "Good weight transfer - you're driving power through your legs."),
]

# Priority ordering for areas to focus on
PRIORITY_ORDER = [
    'hip_rotation_degrees',
    'reachback_depth_score',
    'shoulder_separation_degrees',
    'weight_shift_score',
    'follow_through_score',
]


class FeedbackGenerator:
    """
    Generates coaching feedback from biomechanics metrics.

    Uses rule-based analysis to identify:
    - Areas needing improvement
    - Current strengths
    - Priority focus area
    """

    def __init__(self, skill_level: str = 'intermediate'):
        """
        Initialize feedback generator.

        Args:
            skill_level: 'beginner', 'intermediate', or 'advanced'
                        Adjusts thresholds and feedback complexity
        """
        self.skill_level = skill_level

        # Adjust thresholds based on skill level
        self.threshold_multiplier = {
            'beginner': 0.8,
            'intermediate': 1.0,
            'advanced': 1.15,
        }.get(skill_level, 1.0)

    def generate_feedback(self, metrics: BiomechanicsMetrics) -> PoseFeedback:
        """
        Generate coaching feedback from biomechanics metrics.

        Args:
            metrics: Computed biomechanics metrics

        Returns:
            PoseFeedback with tips, strengths, and priority focus
        """
        tips = []
        strengths = []
        metric_scores = {}

        metrics_dict = metrics.to_dict()

        for metric_name, low_thresh, high_thresh, low_feedback, good_feedback in FEEDBACK_RULES:
            if metric_name not in metrics_dict:
                continue

            value = metrics_dict[metric_name]
            adjusted_low = low_thresh * self.threshold_multiplier
            adjusted_high = high_thresh * self.threshold_multiplier

            if value < adjusted_low:
                tips.append(low_feedback)
                metric_scores[metric_name] = 'low'
            elif value >= adjusted_high:
                strengths.append(good_feedback)
                metric_scores[metric_name] = 'high'
            else:
                metric_scores[metric_name] = 'medium'

        # Determine priority focus area
        priority_focus = self._determine_priority(metric_scores, metrics_dict)

        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)

        # Add general tips if we have few specific ones
        if len(tips) == 0:
            tips.append("Your form looks solid. Focus on consistency and timing.")

        if len(strengths) == 0:
            strengths.append("Keep working on your fundamentals.")

        return PoseFeedback(
            pose_tips=tips[:4],  # Limit to top 4 tips
            priority_focus=priority_focus,
            strengths=strengths[:3],  # Limit to top 3 strengths
            overall_score=overall_score
        )

    def _determine_priority(self, metric_scores: Dict[str, str],
                           metrics_dict: Dict) -> str:
        """
        Determine the highest priority area to focus on.

        Prioritizes based on:
        1. Low-scoring metrics
        2. Importance in the kinetic chain (hips -> shoulders -> arm)
        """
        # Find low-scoring metrics in priority order
        for metric in PRIORITY_ORDER:
            if metric_scores.get(metric) == 'low':
                return self._metric_to_focus_area(metric)

        # If nothing is low, find the lowest medium
        lowest_metric = None
        lowest_value = float('inf')

        for metric in PRIORITY_ORDER:
            if metric in metrics_dict:
                # Normalize score to 0-100 scale
                value = metrics_dict[metric]
                if metric.endswith('_degrees'):
                    value = min(100, value * 2)  # Convert degrees to approx 0-100

                if value < lowest_value:
                    lowest_value = value
                    lowest_metric = metric

        if lowest_metric:
            return self._metric_to_focus_area(lowest_metric)

        return 'timing'  # Default focus

    def _metric_to_focus_area(self, metric_name: str) -> str:
        """Convert metric name to user-friendly focus area."""
        mapping = {
            'reachback_depth_score': 'reachback',
            'hip_rotation_degrees': 'hip_rotation',
            'shoulder_separation_degrees': 'x_factor',
            'follow_through_score': 'follow_through',
            'weight_shift_score': 'weight_transfer',
        }
        return mapping.get(metric_name, metric_name)

    def _calculate_overall_score(self, metrics: BiomechanicsMetrics) -> int:
        """
        Calculate an overall form score (0-100).

        Weighted average of all metrics.
        """
        weights = {
            'reachback_depth_score': 0.20,
            'hip_rotation_degrees': 0.25,  # Hip rotation is crucial
            'shoulder_separation_degrees': 0.20,
            'follow_through_score': 0.15,
            'weight_shift_score': 0.20,
        }

        total_score = 0.0
        total_weight = 0.0

        metrics_dict = metrics.to_dict()

        for metric, weight in weights.items():
            if metric in metrics_dict:
                value = metrics_dict[metric]

                # Normalize degrees to 0-100 scale
                if metric == 'hip_rotation_degrees':
                    value = min(100, (value / 60) * 100)  # 60 degrees = 100
                elif metric == 'shoulder_separation_degrees':
                    value = min(100, (value / 45) * 100)  # 45 degrees = 100

                total_score += value * weight
                total_weight += weight

        if total_weight > 0:
            return int(total_score / total_weight)
        return 50


def generate_combined_feedback(trajectory_feedback: List[str],
                               pose_feedback: PoseFeedback) -> List[str]:
    """
    Combine trajectory-based and pose-based feedback.

    Args:
        trajectory_feedback: Tips from disc trajectory analysis
        pose_feedback: Feedback from pose analysis

    Returns:
        Combined, deduplicated list of feedback tips
    """
    combined = []

    # Add pose tips first (more actionable)
    for tip in pose_feedback.pose_tips:
        if tip not in combined:
            combined.append(tip)

    # Add trajectory feedback
    for tip in trajectory_feedback:
        if tip not in combined:
            combined.append(tip)

    # Limit total tips
    return combined[:6]
