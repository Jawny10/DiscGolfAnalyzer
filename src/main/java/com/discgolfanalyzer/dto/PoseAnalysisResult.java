package com.discgolfanalyzer.dto;

import java.util.Map;

/**
 * DTO for pose analysis metrics from MediaPipe-based analysis.
 */
public class PoseAnalysisResult {

    private boolean detected;
    private PoseMetrics metrics;
    private Map<String, Integer> keyframes;

    public PoseAnalysisResult() {}

    public PoseAnalysisResult(boolean detected, PoseMetrics metrics, Map<String, Integer> keyframes) {
        this.detected = detected;
        this.metrics = metrics;
        this.keyframes = keyframes;
    }

    public boolean isDetected() {
        return detected;
    }

    public void setDetected(boolean detected) {
        this.detected = detected;
    }

    public PoseMetrics getMetrics() {
        return metrics;
    }

    public void setMetrics(PoseMetrics metrics) {
        this.metrics = metrics;
    }

    public Map<String, Integer> getKeyframes() {
        return keyframes;
    }

    public void setKeyframes(Map<String, Integer> keyframes) {
        this.keyframes = keyframes;
    }

    /**
     * Inner class for pose metrics.
     */
    public static class PoseMetrics {
        private int reachbackDepthScore;
        private double hipRotationDegrees;
        private double shoulderSeparationDegrees;
        private int followThroughScore;
        private int weightShiftScore;

        public PoseMetrics() {}

        public int getReachbackDepthScore() {
            return reachbackDepthScore;
        }

        public void setReachbackDepthScore(int reachbackDepthScore) {
            this.reachbackDepthScore = reachbackDepthScore;
        }

        public double getHipRotationDegrees() {
            return hipRotationDegrees;
        }

        public void setHipRotationDegrees(double hipRotationDegrees) {
            this.hipRotationDegrees = hipRotationDegrees;
        }

        public double getShoulderSeparationDegrees() {
            return shoulderSeparationDegrees;
        }

        public void setShoulderSeparationDegrees(double shoulderSeparationDegrees) {
            this.shoulderSeparationDegrees = shoulderSeparationDegrees;
        }

        public int getFollowThroughScore() {
            return followThroughScore;
        }

        public void setFollowThroughScore(int followThroughScore) {
            this.followThroughScore = followThroughScore;
        }

        public int getWeightShiftScore() {
            return weightShiftScore;
        }

        public void setWeightShiftScore(int weightShiftScore) {
            this.weightShiftScore = weightShiftScore;
        }
    }
}
