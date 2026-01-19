package com.discgolfanalyzer.dto;

import java.util.List;

public class AnalyzeRequest {
    private List<String> frameFiles;     // optional
    private double fps;                  // required
    private Integer totalFrames;         // optional
    private Double heightMeters;         // optional
    private Double distanceMeters;       // optional

    public AnalyzeRequest() {}

    public List<String> getFrameFiles() { return frameFiles; }
    public void setFrameFiles(List<String> frameFiles) { this.frameFiles = frameFiles; }

    public double getFps() { return fps; }
    public void setFps(double fps) { this.fps = fps; }

    public Integer getTotalFrames() { return totalFrames; }
    public void setTotalFrames(Integer totalFrames) { this.totalFrames = totalFrames; }

    public Double getHeightMeters() { return heightMeters; }
    public void setHeightMeters(Double heightMeters) { this.heightMeters = heightMeters; }

    public Double getDistanceMeters() { return distanceMeters; }
    public void setDistanceMeters(Double distanceMeters) { this.distanceMeters = distanceMeters; }
}
