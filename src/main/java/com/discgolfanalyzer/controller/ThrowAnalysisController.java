package com.discgolfanalyzer.controller;

import com.discgolfanalyzer.dto.AnalysisResult;
import com.discgolfanalyzer.service.OpenAiVisionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/throws")
public class ThrowAnalysisController {

    private final OpenAiVisionService visionService;

    @Autowired
    public ThrowAnalysisController(OpenAiVisionService visionService) {
        this.visionService = visionService;
    }

    /**
     * Upload a video and analyze the throw.
     */
    @PostMapping(value = "/analyze", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<AnalysisResult> analyzeThrowFromVideo(
            @RequestParam("video") MultipartFile videoFile,
            @RequestParam(value = "fps", defaultValue = "3.0") double fps,
            @RequestParam(value = "maxSeconds", defaultValue = "5") int maxSeconds,
            @RequestParam(value = "hfovDeg", required = false) Double hfovDeg,
            @RequestParam(value = "distanceMeters", required = false) Double distanceMeters
    ) {
        try {
            // Save uploaded video temporarily
            File tempVideo = File.createTempFile("upload-", ".mp4");
            videoFile.transferTo(tempVideo);

            // TODO: implement frame extraction with OpenCV or ffmpeg
            // For now, assume you extracted frames into a list of Paths
            List<Path> frames = extractDummyFrames(tempVideo.toPath());

            // Call vision service
            AnalysisResult result = visionService.analyzeFrames(
                    frames,
                    fps,
                    maxSeconds,
                    hfovDeg,
                    distanceMeters
            );

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError()
                    .body(new AnalysisResult("Error analyzing throw: " + e.getMessage()));
        }
    }

    /**
     * Example dummy frame extractor. Replace with real OpenCV/ffmpeg.
     */
    private List<Path> extractDummyFrames(Path videoPath) throws IOException {
        // In a real implementation: extract frames -> write temp PNGs -> return Paths
        return new ArrayList<>(); // return empty for now
    }
}
