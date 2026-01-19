package com.discgolfanalyzer.service;

import com.discgolfanalyzer.dto.EnhancedAnalysisResult;
import com.discgolfanalyzer.dto.PoseFeedback;
import com.discgolfanalyzer.dto.PoseAnalysisResult;
import com.discgolfanalyzer.dto.TrajectoryResult;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Optional service for enhancing disc golf analysis feedback using Anthropic's Claude.
 *
 * When enabled, takes the structured pose/trajectory analysis and generates
 * natural language coaching feedback and summaries.
 */
@Service
@ConditionalOnProperty(name = "anthropic.enabled", havingValue = "true", matchIfMissing = false)
public class AnthropicVisionService {

    private static final Logger logger = LoggerFactory.getLogger(AnthropicVisionService.class);
    private static final String ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages";

    private final RestTemplate restTemplate;

    @Value("${anthropic.api-key:#{environment.ANTHROPIC_API_KEY}}")
    private String apiKey;

    @Value("${anthropic.model:claude-sonnet-4-20250514}")
    private String model;

    @Value("${anthropic.max-tokens:1024}")
    private int maxTokens;

    public AnthropicVisionService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Enhance analysis result with AI-generated natural language feedback.
     *
     * @param result The structured analysis result from MediaPipe/biomechanics
     * @return The same result with AI-enhanced summary and combined tips
     */
    public EnhancedAnalysisResult enhanceWithAI(EnhancedAnalysisResult result) {
        if (apiKey == null || apiKey.isBlank()) {
            logger.warn("Anthropic API key not configured, skipping AI enhancement");
            return result;
        }

        try {
            String prompt = buildPrompt(result);
            String aiResponse = callClaudeAPI(prompt);

            if (aiResponse != null && !aiResponse.isBlank()) {
                result.setAiEnhancedSummary(aiResponse);

                // Combine AI insights with existing tips
                List<String> combinedTips = combineTips(result, aiResponse);
                result.setCombinedTips(combinedTips);
            }

        } catch (Exception e) {
            logger.error("Error enhancing analysis with Claude: {}", e.getMessage());
            // Don't fail - just return the original result without AI enhancement
        }

        return result;
    }

    /**
     * Generate a coaching summary for the throw analysis.
     */
    public String generateCoachingSummary(EnhancedAnalysisResult result) {
        if (apiKey == null || apiKey.isBlank()) {
            return null;
        }

        String prompt = buildCoachingPrompt(result);
        return callClaudeAPI(prompt);
    }

    private String buildPrompt(EnhancedAnalysisResult result) {
        StringBuilder sb = new StringBuilder();
        sb.append("You are an expert disc golf coach analyzing a player's throw. ");
        sb.append("Based on the following biomechanics data, provide a brief, encouraging coaching summary ");
        sb.append("(2-3 sentences) and your top priority recommendation.\n\n");

        // Add trajectory data
        TrajectoryResult traj = result.getTrajectory();
        if (traj != null) {
            sb.append("TRAJECTORY:\n");
            sb.append("- Flight path: ").append(traj.getFlightPath()).append("\n");
            sb.append("- Distance: ").append(traj.getDistance()).append(" units\n");
            sb.append("- Release angle: ").append(traj.getReleaseAngle()).append(" degrees\n\n");
        }

        // Add pose metrics
        PoseAnalysisResult pose = result.getPose();
        if (pose != null && pose.isDetected() && pose.getMetrics() != null) {
            PoseAnalysisResult.PoseMetrics m = pose.getMetrics();
            sb.append("BIOMECHANICS SCORES (0-100):\n");
            sb.append("- Reachback depth: ").append(m.getReachbackDepthScore()).append("\n");
            sb.append("- Hip rotation: ").append(m.getHipRotationDegrees()).append(" degrees\n");
            sb.append("- Shoulder separation (X-factor): ").append(m.getShoulderSeparationDegrees()).append(" degrees\n");
            sb.append("- Follow-through: ").append(m.getFollowThroughScore()).append("\n");
            sb.append("- Weight shift: ").append(m.getWeightShiftScore()).append("\n\n");
        }

        // Add existing feedback
        PoseFeedback feedback = result.getFeedback();
        if (feedback != null) {
            sb.append("PRIORITY FOCUS AREA: ").append(feedback.getPriorityFocus()).append("\n");
            sb.append("OVERALL SCORE: ").append(feedback.getOverallScore()).append("/100\n\n");

            if (feedback.getPoseTips() != null && !feedback.getPoseTips().isEmpty()) {
                sb.append("RULE-BASED TIPS:\n");
                for (String tip : feedback.getPoseTips()) {
                    sb.append("- ").append(tip).append("\n");
                }
            }
        }

        sb.append("\nProvide your coaching feedback in a friendly, supportive tone. ");
        sb.append("Focus on the most impactful change they can make.");

        return sb.toString();
    }

    private String buildCoachingPrompt(EnhancedAnalysisResult result) {
        StringBuilder sb = new StringBuilder();
        sb.append("As an experienced disc golf instructor, provide a detailed but concise analysis ");
        sb.append("of this throw. Include:\n");
        sb.append("1. What the player is doing well\n");
        sb.append("2. The single most important area to improve\n");
        sb.append("3. A specific drill or exercise to practice\n\n");

        // Include all the same data as above
        sb.append(buildPrompt(result));

        return sb.toString();
    }

    private String callClaudeAPI(String prompt) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("x-api-key", apiKey);
        headers.set("anthropic-version", "2023-06-01");

        Map<String, Object> message = new HashMap<>();
        message.put("role", "user");
        message.put("content", prompt);

        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", model);
        requestBody.put("max_tokens", maxTokens);
        requestBody.put("messages", List.of(message));

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(
                    ANTHROPIC_API_URL, request, Map.class);

            if (response.getBody() != null) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> content = (List<Map<String, Object>>)
                        response.getBody().get("content");

                if (content != null && !content.isEmpty()) {
                    return (String) content.get(0).get("text");
                }
            }
        } catch (Exception e) {
            logger.error("Claude API call failed: {}", e.getMessage());
        }

        return null;
    }

    private List<String> combineTips(EnhancedAnalysisResult result, String aiResponse) {
        List<String> combined = new ArrayList<>();

        // Add AI-generated insight first (if it's not too long)
        if (aiResponse.length() < 300) {
            combined.add(aiResponse);
        } else {
            // Extract first sentence as the key insight
            int firstPeriod = aiResponse.indexOf('.');
            if (firstPeriod > 0 && firstPeriod < 200) {
                combined.add(aiResponse.substring(0, firstPeriod + 1));
            }
        }

        // Add pose-based tips
        PoseFeedback feedback = result.getFeedback();
        if (feedback != null && feedback.getPoseTips() != null) {
            combined.addAll(feedback.getPoseTips());
        }

        // Add trajectory-based tips
        TrajectoryResult trajectory = result.getTrajectory();
        if (trajectory != null && trajectory.getTechniqueFeedback() != null) {
            for (String tip : trajectory.getTechniqueFeedback()) {
                if (!combined.contains(tip)) {
                    combined.add(tip);
                }
            }
        }

        // Limit total tips
        return combined.stream().limit(6).collect(Collectors.toList());
    }
}
