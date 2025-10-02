package com.discgolfanalyzer.dto;

import java.util.List;

public class AnalysisResult {
    private String summary;
    private Double releaseSpeedMph;
    private List<String> techniqueFeedback;

    public AnalysisResult() {}

    public AnalysisResult(String summary, Double releaseSpeedMph, List<String> techniqueFeedback) {
        this.summary = summary;
        this.releaseSpeedMph = releaseSpeedMph;
        this.techniqueFeedback = techniqueFeedback;
    }

    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }

    public Double getReleaseSpeedMph() { return releaseSpeedMph; }
    public void setReleaseSpeedMph(Double releaseSpeedMph) { this.releaseSpeedMph = releaseSpeedMph; }

    public List<String> getTechniqueFeedback() { return techniqueFeedback; }
    public void setTechniqueFeedback(List<String> techniqueFeedback) { this.techniqueFeedback = techniqueFeedback; }
}
