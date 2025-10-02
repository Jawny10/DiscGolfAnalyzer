// src/main/java/com/discgolfanalyzer/model/ThrowAnalysis.java
package com.discgolfanalyzer.model;

import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Data
public class ThrowAnalysis {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne
    private AppUser user;
    
    private LocalDateTime timestamp;
    private String videoUrl;
    private Double distance;
    private String flightPath;
    private Double maxHeight;
    private Double initialVelocity;
    
    @ElementCollection
    private List<String> techniqueFeedback = new ArrayList<>();
}