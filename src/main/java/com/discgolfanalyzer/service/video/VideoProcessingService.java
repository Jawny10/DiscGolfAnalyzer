package com.discgolfanalyzer.service.video;

import com.discgolfanalyzer.dto.*;
import com.discgolfanalyzer.model.ThrowAnalysis;
import com.discgolfanalyzer.model.AppUser;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
public class VideoProcessingService {
    private static final Logger logger = LoggerFactory.getLogger(VideoProcessingService.class);

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    @Value("${ml.service.url}")
    private String mlServiceUrl; // e.g. http://localhost:5001

    @Value("${ml.service.mock:false}")
    private boolean mockEnabled; // allow forcing mock replies

    @Value("${analysis.pose.enabled:true}")
    private boolean poseAnalysisEnabled;

    @Value("${analysis.pose.min-confidence:0.5}")
    private double poseMinConfidence;

    public ThrowAnalysis processVideo(
            MultipartFile videoFile,
            AppUser user,
            Double fps,
            Integer maxSeconds,
            Double hfovDeg,
            Double distanceMeters
    ) throws IOException {

        logger.info("Processing video for user: {}", user.getUsername());

        // If mock is forced, skip the call and synthesize
        if (mockEnabled) {
            logger.warn("ml.service.mock=true: returning synthetic analysis without calling ML service.");
            return synthesizeResult(user, fps, maxSeconds, hfovDeg, distanceMeters, "mock-forced");
        }

        // Prepare headers
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        // Video as ByteArrayResource so filename is preserved
        ByteArrayResource videoResource = new ByteArrayResource(videoFile.getBytes()) {
            @Override public String getFilename() {
                return videoFile.getOriginalFilename();
            }
        };

        // Build form-data body
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("video", videoResource);

        // Forward numeric params if provided
        if (fps != null) {
            body.add("fps", fps.toString());
        }
        if (maxSeconds != null) {
            body.add("maxSeconds", maxSeconds.toString());
            body.add("max_seconds", maxSeconds.toString());
        }
        if (hfovDeg != null) {
            body.add("hfovDeg", hfovDeg.toString());
            body.add("hfov_deg", hfovDeg.toString());
        }
        if (distanceMeters != null) {
            body.add("distanceMeters", distanceMeters.toString());
            body.add("distance_meters", distanceMeters.toString());
        }

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        String url = mlServiceUrl.endsWith("/") ? mlServiceUrl + "analyze" : mlServiceUrl + "/analyze";
        logger.info("Sending video to ML service: {}", url);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, requestEntity, Map.class);
            Map<?, ?> analysis = response.getBody();
            logger.info("ML service response (status {}): {}", response.getStatusCode(), analysis);
            return mapToThrowAnalysis(user, analysis);

        } catch (ResourceAccessException connectEx) {
            // Connection refused / timeout, etc.
            logger.error("Cannot reach ML service at {}. Using synthetic analysis.", url, connectEx);
            return synthesizeResult(user, fps, maxSeconds, hfovDeg, distanceMeters, "connect-failed");

        } catch (HttpStatusCodeException ex) {
            // Upstream returned 4xx/5xx with a body
            logger.error("ML service returned {} with body: {}", ex.getStatusCode(), ex.getResponseBodyAsString());
            // If desired, fall back to synthetic here too:
            return synthesizeResult(user, fps, maxSeconds, hfovDeg, distanceMeters, "upstream-" + ex.getStatusCode());

        } catch (Exception e) {
            logger.error("Unexpected error communicating with ML service", e);
            // Safe fallback instead of bubbling 500 to the client
            return synthesizeResult(user, fps, maxSeconds, hfovDeg, distanceMeters, "unexpected-error");
        }
    }

    private ThrowAnalysis mapToThrowAnalysis(AppUser user, Map<?, ?> analysis) {
        ThrowAnalysis ta = base(user);

        if (analysis != null) {
            Object distance = opt(analysis, "distance", "distanceMeters");
            if (distance instanceof Number) ta.setDistance(((Number) distance).doubleValue());

            Object flightPath = analysis.get("flightPath");
            if (flightPath instanceof String) ta.setFlightPath((String) flightPath);

            Object maxHeight = opt(analysis, "maxHeight", "max_height");
            if (maxHeight instanceof Number) ta.setMaxHeight(((Number) maxHeight).doubleValue());

            Object releaseAngle = opt(analysis, "releaseAngle", "release_angle");
            if (releaseAngle instanceof Number) ta.setInitialVelocity(((Number) releaseAngle).doubleValue());

            Object feedback = analysis.get("techniqueFeedback");
            if (feedback instanceof List) {
                @SuppressWarnings("unchecked")
                List<String> tips = (List<String>) feedback;
                ta.setTechniqueFeedback(tips);
            }

            if (ta.getFlightPath() == null && analysis.get("summary") instanceof String) {
                ta.setFlightPath((String) analysis.get("summary"));
            }
        }

        return ta;
    }

    private Object opt(Map<?, ?> map, String primary, String secondary) {
        if (map.containsKey(primary)) return map.get(primary);
        return map.get(secondary);
    }

    private ThrowAnalysis base(AppUser user) {
        ThrowAnalysis ta = new ThrowAnalysis();
        ta.setUser(user);
        ta.setTimestamp(LocalDateTime.now());
        ta.setVideoUrl("local-upload"); // replace with storage URL later
        return ta;
    }

    private ThrowAnalysis synthesizeResult(
            AppUser user,
            Double fps,
            Integer maxSeconds,
            Double hfovDeg,
            Double distanceMeters,
            String reason
    ) {
        // Very basic “plausible” values so you can exercise the UI and DB path.
        double dist = (distanceMeters != null ? distanceMeters : 12.0) * 7.0; // pretend throw distance ~= 7x frame distance
        double maxH = Math.max(2.8, Math.min(6.0, (hfovDeg != null ? hfovDeg / 20.0 : 3.9)));
        double rel = 10.0 + (fps != null ? Math.min(10.0, fps / 6.0) : 3.0);

        ThrowAnalysis ta = base(user);
        ta.setDistance(round1(dist));
        ta.setMaxHeight(round1(maxH));
        ta.setInitialVelocity(round1(rel));
        ta.setFlightPath("synthetic: slight hyzer (fallback: " + reason + ")");
        ta.setTechniqueFeedback(Arrays.asList(
                "Shift weight earlier into the plant.",
                "Keep shoulders closed a touch longer.",
                "Watch nose angle at release."
        ));
        logger.info("Returning synthetic ThrowAnalysis (reason={}): dist={}m, maxH={}m, relAngle={}",
                reason, ta.getDistance(), ta.getMaxHeight(), ta.getInitialVelocity());
        return ta;
    }

    private double round1(double v) {
        return Math.round(v * 10.0) / 10.0;
    }

    /**
     * Process video with enhanced pose analysis.
     *
     * Calls the /analyze-pose endpoint which combines:
     * - Disc trajectory detection
     * - MediaPipe pose extraction
     * - Biomechanics analysis
     * - Rule-based feedback generation
     */
    public EnhancedAnalysisResult processVideoEnhanced(
            MultipartFile videoFile,
            String handedness,
            String skillLevel
    ) throws IOException {

        logger.info("Processing video with enhanced pose analysis");

        if (!poseAnalysisEnabled) {
            logger.warn("Pose analysis is disabled, returning basic result");
            return createBasicResult("Pose analysis is disabled");
        }

        if (mockEnabled) {
            logger.warn("Mock mode enabled, returning synthetic enhanced result");
            return createMockEnhancedResult();
        }

        // Prepare multipart request
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        ByteArrayResource videoResource = new ByteArrayResource(videoFile.getBytes()) {
            @Override
            public String getFilename() {
                return videoFile.getOriginalFilename();
            }
        };

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("video", videoResource);
        body.add("min_confidence", String.valueOf(poseMinConfidence));
        body.add("handedness", handedness != null ? handedness : "right");
        body.add("skill_level", skillLevel != null ? skillLevel : "intermediate");

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        String url = mlServiceUrl.endsWith("/") ? mlServiceUrl + "analyze-pose" : mlServiceUrl + "/analyze-pose";

        logger.info("Sending video to pose analysis endpoint: {}", url);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, requestEntity, Map.class);
            Map<?, ?> responseBody = response.getBody();
            logger.info("Pose analysis response (status {})", response.getStatusCode());

            return mapToEnhancedResult(responseBody);

        } catch (ResourceAccessException connectEx) {
            logger.error("Cannot reach ML service at {}: {}", url, connectEx.getMessage());
            return createBasicResult("ML service unavailable: " + connectEx.getMessage());

        } catch (HttpStatusCodeException ex) {
            logger.error("ML service returned {} with body: {}", ex.getStatusCode(), ex.getResponseBodyAsString());
            return createBasicResult("ML service error: " + ex.getStatusCode());

        } catch (Exception e) {
            logger.error("Unexpected error during pose analysis", e);
            return createBasicResult("Unexpected error: " + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private EnhancedAnalysisResult mapToEnhancedResult(Map<?, ?> response) {
        EnhancedAnalysisResult.Builder builder = EnhancedAnalysisResult.builder();

        if (response == null) {
            return createBasicResult("Empty response from ML service");
        }

        // Map trajectory
        Map<?, ?> trajectoryMap = (Map<?, ?>) response.get("trajectory");
        if (trajectoryMap != null) {
            TrajectoryResult trajectory = new TrajectoryResult();
            trajectory.setFlightPath(getStringOrDefault(trajectoryMap, "flightPath", "unknown"));
            trajectory.setDistance(getDoubleOrDefault(trajectoryMap, "distance", 0.0));
            trajectory.setMaxHeight(getDoubleOrDefault(trajectoryMap, "maxHeight", 0.0));
            trajectory.setReleaseAngle(getDoubleOrDefault(trajectoryMap, "releaseAngle", 0.0));
            trajectory.setTechniqueFeedback((List<String>) trajectoryMap.get("techniqueFeedback"));
            builder.trajectory(trajectory);
        }

        // Map pose
        Map<?, ?> poseMap = (Map<?, ?>) response.get("pose");
        if (poseMap != null) {
            PoseAnalysisResult pose = new PoseAnalysisResult();
            pose.setDetected(getBooleanOrDefault(poseMap, "detected", false));

            Map<?, ?> metricsMap = (Map<?, ?>) poseMap.get("metrics");
            if (metricsMap != null) {
                PoseAnalysisResult.PoseMetrics metrics = new PoseAnalysisResult.PoseMetrics();
                metrics.setReachbackDepthScore(getIntOrDefault(metricsMap, "reachback_depth_score", 0));
                metrics.setHipRotationDegrees(getDoubleOrDefault(metricsMap, "hip_rotation_degrees", 0.0));
                metrics.setShoulderSeparationDegrees(getDoubleOrDefault(metricsMap, "shoulder_separation_degrees", 0.0));
                metrics.setFollowThroughScore(getIntOrDefault(metricsMap, "follow_through_score", 0));
                metrics.setWeightShiftScore(getIntOrDefault(metricsMap, "weight_shift_score", 0));
                pose.setMetrics(metrics);
            }

            Map<?, ?> keyframesMap = (Map<?, ?>) poseMap.get("keyframes");
            if (keyframesMap != null) {
                Map<String, Integer> keyframes = new HashMap<>();
                for (Map.Entry<?, ?> entry : keyframesMap.entrySet()) {
                    if (entry.getValue() instanceof Number) {
                        keyframes.put(entry.getKey().toString(), ((Number) entry.getValue()).intValue());
                    }
                }
                pose.setKeyframes(keyframes);
            }

            builder.pose(pose);
        }

        // Map feedback
        Map<?, ?> feedbackMap = (Map<?, ?>) response.get("feedback");
        if (feedbackMap != null) {
            PoseFeedback feedback = new PoseFeedback();
            feedback.setPoseTips((List<String>) feedbackMap.get("pose_tips"));
            feedback.setPriorityFocus(getStringOrDefault(feedbackMap, "priority_focus", "general"));
            feedback.setStrengths((List<String>) feedbackMap.get("strengths"));
            feedback.setOverallScore(getIntOrDefault(feedbackMap, "overall_score", 0));
            builder.feedback(feedback);
        }

        // Processing time
        builder.processingTimeMs(getIntOrDefault(response, "processingTimeMs", 0));

        return builder.build();
    }

    private EnhancedAnalysisResult createBasicResult(String errorMessage) {
        TrajectoryResult trajectory = new TrajectoryResult();
        trajectory.setFlightPath("unavailable");
        trajectory.setDistance(0);
        trajectory.setMaxHeight(0);
        trajectory.setReleaseAngle(0);
        trajectory.setTechniqueFeedback(Arrays.asList(errorMessage));

        PoseAnalysisResult pose = new PoseAnalysisResult();
        pose.setDetected(false);
        pose.setMetrics(new PoseAnalysisResult.PoseMetrics());
        pose.setKeyframes(Collections.emptyMap());

        PoseFeedback feedback = new PoseFeedback();
        feedback.setPoseTips(Arrays.asList("Analysis unavailable. " + errorMessage));
        feedback.setPriorityFocus("error");
        feedback.setStrengths(Collections.emptyList());
        feedback.setOverallScore(0);

        return EnhancedAnalysisResult.builder()
                .trajectory(trajectory)
                .pose(pose)
                .feedback(feedback)
                .processingTimeMs(0)
                .build();
    }

    private EnhancedAnalysisResult createMockEnhancedResult() {
        TrajectoryResult trajectory = new TrajectoryResult();
        trajectory.setFlightPath("hyzer");
        trajectory.setDistance(85.5);
        trajectory.setMaxHeight(12.3);
        trajectory.setReleaseAngle(15.0);
        trajectory.setTechniqueFeedback(Arrays.asList(
                "Your throw has a hyzer angle, good for controlled fades.",
                "Focus on a smooth release and follow-through."
        ));

        PoseAnalysisResult.PoseMetrics metrics = new PoseAnalysisResult.PoseMetrics();
        metrics.setReachbackDepthScore(72);
        metrics.setHipRotationDegrees(38.5);
        metrics.setShoulderSeparationDegrees(32.0);
        metrics.setFollowThroughScore(68);
        metrics.setWeightShiftScore(75);

        PoseAnalysisResult pose = new PoseAnalysisResult();
        pose.setDetected(true);
        pose.setMetrics(metrics);
        Map<String, Integer> keyframes = new HashMap<>();
        keyframes.put("setup", 0);
        keyframes.put("reachback", 15);
        keyframes.put("release", 28);
        keyframes.put("follow_through", 40);
        pose.setKeyframes(keyframes);

        PoseFeedback feedback = new PoseFeedback();
        feedback.setPoseTips(Arrays.asList(
                "Rotate your hips more during the throw. Lead with your hips, not your arm.",
                "Follow through more completely. Let your arm continue across your body after release."
        ));
        feedback.setPriorityFocus("hip_rotation");
        feedback.setStrengths(Arrays.asList(
                "Good weight transfer - you're driving power through your legs."
        ));
        feedback.setOverallScore(65);

        return EnhancedAnalysisResult.builder()
                .trajectory(trajectory)
                .pose(pose)
                .feedback(feedback)
                .processingTimeMs(1250)
                .build();
    }

    // Helper methods for safe type conversion
    private String getStringOrDefault(Map<?, ?> map, String key, String defaultValue) {
        Object value = map.get(key);
        return value instanceof String ? (String) value : defaultValue;
    }

    private double getDoubleOrDefault(Map<?, ?> map, String key, double defaultValue) {
        Object value = map.get(key);
        return value instanceof Number ? ((Number) value).doubleValue() : defaultValue;
    }

    private int getIntOrDefault(Map<?, ?> map, String key, int defaultValue) {
        Object value = map.get(key);
        return value instanceof Number ? ((Number) value).intValue() : defaultValue;
    }

    private boolean getBooleanOrDefault(Map<?, ?> map, String key, boolean defaultValue) {
        Object value = map.get(key);
        return value instanceof Boolean ? (Boolean) value : defaultValue;
    }
}
