package com.discgolfanalyzer.dto;

import java.util.List;

/**
 * DTO for pose-based feedback from biomechanics analysis.
 */
public class PoseFeedback {

    private List<String> poseTips;
    private String priorityFocus;
    private List<String> strengths;
    private int overallScore;

    public PoseFeedback() {}

    public PoseFeedback(List<String> poseTips, String priorityFocus,
                        List<String> strengths, int overallScore) {
        this.poseTips = poseTips;
        this.priorityFocus = priorityFocus;
        this.strengths = strengths;
        this.overallScore = overallScore;
    }

    public List<String> getPoseTips() {
        return poseTips;
    }

    public void setPoseTips(List<String> poseTips) {
        this.poseTips = poseTips;
    }

    public String getPriorityFocus() {
        return priorityFocus;
    }

    public void setPriorityFocus(String priorityFocus) {
        this.priorityFocus = priorityFocus;
    }

    public List<String> getStrengths() {
        return strengths;
    }

    public void setStrengths(List<String> strengths) {
        this.strengths = strengths;
    }

    public int getOverallScore() {
        return overallScore;
    }

    public void setOverallScore(int overallScore) {
        this.overallScore = overallScore;
    }
}
