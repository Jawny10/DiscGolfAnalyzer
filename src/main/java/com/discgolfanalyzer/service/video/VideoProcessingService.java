package com.discgolfanalyzer.service.video;

import com.discgolfanalyzer.model.ThrowAnalysis;
import com.discgolfanalyzer.model.AppUser;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class VideoProcessingService {
    private static final Logger logger = LoggerFactory.getLogger(VideoProcessingService.class);
    
    private final RestTemplate restTemplate;
    
    @Value("${ml.service.url}")
    private String mlServiceUrl;
    
    public ThrowAnalysis processVideo(MultipartFile videoFile, AppUser user) throws IOException {
        logger.info("Processing video for user: {}", user.getUsername());
        
        // Prepare HTTP headers
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        
        // Prepare the parts
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        ByteArrayResource videoResource = new ByteArrayResource(videoFile.getBytes()) {
            @Override
            public String getFilename() {
                return videoFile.getOriginalFilename();
            }
        };
        
        logger.info("Video file name: {}, size: {}", videoFile.getOriginalFilename(), videoFile.getSize());
        body.add("video", videoResource);
        
        // Create the HTTP entity
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        
        try {
            // Send POST request to ML service
            logger.info("Sending video to ML service at: {}", mlServiceUrl + "/analyze");
            ResponseEntity<HashMap> response = restTemplate.postForEntity(
                    mlServiceUrl + "/analyze",
                    requestEntity,
                    HashMap.class
            );
            
            // Process response
            @SuppressWarnings("unchecked")
            Map<String, Object> analysisResult = (Map<String, Object>) response.getBody();
            logger.info("Received response from ML service: {}", analysisResult);
            
            // Create ThrowAnalysis object
            ThrowAnalysis throwAnalysis = new ThrowAnalysis();
            throwAnalysis.setUser(user);
            throwAnalysis.setTimestamp(LocalDateTime.now());
            throwAnalysis.setVideoUrl("temp_url"); // Would be replaced with S3 URL after upload
            
            // Set analysis data
            throwAnalysis.setDistance((Double) analysisResult.get("distance"));
            throwAnalysis.setFlightPath((String) analysisResult.get("flightPath"));
            throwAnalysis.setMaxHeight((Double) analysisResult.get("maxHeight"));
            throwAnalysis.setInitialVelocity((Double) analysisResult.get("releaseAngle")); // Using initialVelocity field for release angle
            
            // Set technique feedback
            @SuppressWarnings("unchecked")
            List<String> feedback = (List<String>) analysisResult.get("techniqueFeedback");
            throwAnalysis.setTechniqueFeedback(feedback);
            
            return throwAnalysis;
        } catch (Exception e) {
            logger.error("Error communicating with ML service", e);
            throw new IOException("Error communicating with ML service: " + e.getMessage());
        }
    }
}