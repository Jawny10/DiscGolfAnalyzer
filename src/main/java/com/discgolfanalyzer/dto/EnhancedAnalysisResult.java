package com.discgolfanalyzer.dto;

import java.util.List;

/**
 * DTO for combined trajectory + pose + AI-enhanced analysis results.
 */
public class EnhancedAnalysisResult {

    private TrajectoryResult trajectory;
    private PoseAnalysisResult pose;
    private PoseFeedback feedback;
    private String aiEnhancedSummary;
    private List<String> combinedTips;
    private int processingTimeMs;

    public EnhancedAnalysisResult() {}

    public TrajectoryResult getTrajectory() {
        return trajectory;
    }

    public void setTrajectory(TrajectoryResult trajectory) {
        this.trajectory = trajectory;
    }

    public PoseAnalysisResult getPose() {
        return pose;
    }

    public void setPose(PoseAnalysisResult pose) {
        this.pose = pose;
    }

    public PoseFeedback getFeedback() {
        return feedback;
    }

    public void setFeedback(PoseFeedback feedback) {
        this.feedback = feedback;
    }

    public String getAiEnhancedSummary() {
        return aiEnhancedSummary;
    }

    public void setAiEnhancedSummary(String aiEnhancedSummary) {
        this.aiEnhancedSummary = aiEnhancedSummary;
    }

    public List<String> getCombinedTips() {
        return combinedTips;
    }

    public void setCombinedTips(List<String> combinedTips) {
        this.combinedTips = combinedTips;
    }

    public int getProcessingTimeMs() {
        return processingTimeMs;
    }

    public void setProcessingTimeMs(int processingTimeMs) {
        this.processingTimeMs = processingTimeMs;
    }

    /**
     * Builder for fluent construction.
     */
    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private final EnhancedAnalysisResult result = new EnhancedAnalysisResult();

        public Builder trajectory(TrajectoryResult trajectory) {
            result.trajectory = trajectory;
            return this;
        }

        public Builder pose(PoseAnalysisResult pose) {
            result.pose = pose;
            return this;
        }

        public Builder feedback(PoseFeedback feedback) {
            result.feedback = feedback;
            return this;
        }

        public Builder aiEnhancedSummary(String summary) {
            result.aiEnhancedSummary = summary;
            return this;
        }

        public Builder combinedTips(List<String> tips) {
            result.combinedTips = tips;
            return this;
        }

        public Builder processingTimeMs(int ms) {
            result.processingTimeMs = ms;
            return this;
        }

        public EnhancedAnalysisResult build() {
            return result;
        }
    }
}
