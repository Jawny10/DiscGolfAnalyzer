// src/main/java/com/discgolfanalyzer/repository/ThrowAnalysisRepository.java
package com.discgolfanalyzer.repository;

import com.discgolfanalyzer.model.ThrowAnalysis;
import com.discgolfanalyzer.model.AppUser;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ThrowAnalysisRepository extends JpaRepository<ThrowAnalysis, Long> {
    List<ThrowAnalysis> findByUserOrderByTimestampDesc(AppUser user);
}