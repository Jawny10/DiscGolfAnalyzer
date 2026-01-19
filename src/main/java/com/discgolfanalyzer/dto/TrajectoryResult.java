package com.discgolfanalyzer.dto;

import java.util.List;

/**
 * DTO for disc trajectory analysis results.
 */
public class TrajectoryResult {

    private String flightPath;
    private double distance;
    private double maxHeight;
    private double releaseAngle;
    private List<String> techniqueFeedback;

    public TrajectoryResult() {}

    public TrajectoryResult(String flightPath, double distance, double maxHeight,
                            double releaseAngle, List<String> techniqueFeedback) {
        this.flightPath = flightPath;
        this.distance = distance;
        this.maxHeight = maxHeight;
        this.releaseAngle = releaseAngle;
        this.techniqueFeedback = techniqueFeedback;
    }

    public String getFlightPath() {
        return flightPath;
    }

    public void setFlightPath(String flightPath) {
        this.flightPath = flightPath;
    }

    public double getDistance() {
        return distance;
    }

    public void setDistance(double distance) {
        this.distance = distance;
    }

    public double getMaxHeight() {
        return maxHeight;
    }

    public void setMaxHeight(double maxHeight) {
        this.maxHeight = maxHeight;
    }

    public double getReleaseAngle() {
        return releaseAngle;
    }

    public void setReleaseAngle(double releaseAngle) {
        this.releaseAngle = releaseAngle;
    }

    public List<String> getTechniqueFeedback() {
        return techniqueFeedback;
    }

    public void setTechniqueFeedback(List<String> techniqueFeedback) {
        this.techniqueFeedback = techniqueFeedback;
    }
}
