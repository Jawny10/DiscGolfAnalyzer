package com.discgolfanalyzer.controller;

import com.discgolfanalyzer.dto.EnhancedAnalysisResult;
import com.discgolfanalyzer.model.AppUser;
import com.discgolfanalyzer.model.ThrowAnalysis;
import com.discgolfanalyzer.repository.UserRepository;
import com.discgolfanalyzer.service.AnthropicVisionService;
import com.discgolfanalyzer.service.video.VideoProcessingService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/throws")
@RequiredArgsConstructor
public class ThrowAnalysisController {

    private static final Logger log = LoggerFactory.getLogger(ThrowAnalysisController.class);

    private final VideoProcessingService videoProcessingService;
    private final UserRepository userRepository;

    // Optional - only injected if anthropic.enabled=true
    @Autowired(required = false)
    private AnthropicVisionService anthropicVisionService;

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("OK");
    }

    @PostMapping(value = "/analyze", consumes = {"multipart/form-data"})
    public ResponseEntity<ThrowAnalysis> analyze(
            @RequestPart("video") MultipartFile video,
            @RequestParam(name = "fps", required = false) Double fps,
            @RequestParam(name = "maxSeconds", required = false) Integer maxSeconds,
            @RequestParam(name = "hfovDeg", required = false) Double hfovDeg,
            @RequestParam(name = "distanceMeters", required = false) Double distanceMeters,
            @AuthenticationPrincipal AppUser authedUser // if you aren’t using Spring Security auth yet, replace with a lookup or stub
    ) throws Exception {

        // If you don’t have auth wired, you can stub a user for now:
        AppUser user = authedUser != null ? authedUser : userRepository.findAll().stream().findFirst().orElseGet(() -> {
            AppUser u = new AppUser();
            u.setUsername("demo");
            u.setEmail("demo@example.com");
            return userRepository.save(u);
        });

        log.info("Analyze called: fps={}, maxSeconds={}, hfovDeg={}, distanceMeters={}", fps, maxSeconds, hfovDeg, distanceMeters);

        ThrowAnalysis result = videoProcessingService.processVideo(
                video,
                user,
                fps,
                maxSeconds,
                hfovDeg,
                distanceMeters
        );

        return ResponseEntity.ok(result);
    }

    /**
     * Enhanced analysis endpoint with pose detection and optional AI enhancement.
     *
     * Uses MediaPipe for pose extraction and biomechanics analysis.
     * Optionally enhances feedback with Anthropic Claude if enabled.
     *
     * @param video The video file to analyze
     * @param handedness Player's throwing hand ("right" or "left")
     * @param skillLevel Player's skill level ("beginner", "intermediate", "advanced")
     * @return Enhanced analysis with trajectory, pose metrics, and coaching feedback
     */
    @PostMapping(value = "/analyze-enhanced", consumes = {"multipart/form-data"})
    public ResponseEntity<EnhancedAnalysisResult> analyzeEnhanced(
            @RequestPart("video") MultipartFile video,
            @RequestParam(name = "handedness", required = false, defaultValue = "right") String handedness,
            @RequestParam(name = "skillLevel", required = false, defaultValue = "intermediate") String skillLevel
    ) throws Exception {

        log.info("Enhanced analyze called: handedness={}, skillLevel={}", handedness, skillLevel);

        // Call the enhanced processing pipeline
        EnhancedAnalysisResult result = videoProcessingService.processVideoEnhanced(
                video,
                handedness,
                skillLevel
        );

        // Optionally enhance with AI (Claude) if available
        if (anthropicVisionService != null) {
            log.info("Enhancing analysis with Anthropic Claude");
            result = anthropicVisionService.enhanceWithAI(result);
        } else {
            log.debug("Anthropic service not enabled, skipping AI enhancement");
        }

        return ResponseEntity.ok(result);
    }
}
