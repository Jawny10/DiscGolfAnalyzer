package com.discgolfanalyzer.dto;

import java.util.Collections;
import java.util.List;

public class AnalysisResult {
    private String summary;
    private Double score;
    private List<String> tips;

    public AnalysisResult() { }

    public AnalysisResult(String summary, Double score, List<String> tips) {
        this.summary = summary;
        this.score = score;
        this.tips = tips;
    }

    // Convenience 1-arg ctor used by controller
    public AnalysisResult(String summary) {
        this(summary, null, Collections.emptyList());
    }

    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }

    public Double getScore() { return score; }
    public void setScore(Double score) { this.score = score; }

    public List<String> getTips() { return tips; }
    public void setTips(List<String> tips) { this.tips = tips; }
}
