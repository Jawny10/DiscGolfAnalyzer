// src/main/java/com/discgolfanalyzer/controller/UserController.java
package com.discgolfanalyzer.controller;

import com.discgolfanalyzer.model.AppUser;
import com.discgolfanalyzer.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @PostMapping("/register")
    public ResponseEntity<?> registerUser(@RequestBody AppUser user) {
        // Validate request
        if (userRepository.existsByUsername(user.getUsername())) {
            return ResponseEntity.badRequest().body("Username already taken");
        }
        
        if (userRepository.existsByEmail(user.getEmail())) {
            return ResponseEntity.badRequest().body("Email already in use");
        }

        // Encode password and save user
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        AppUser savedUser = userRepository.save(user);
        
        // Return user without password
        Map<String, Object> response = new HashMap<>();
        response.put("id", savedUser.getId());
        response.put("username", savedUser.getUsername());
        response.put("email", savedUser.getEmail());
        
        return ResponseEntity.ok(response);

    
    }
    // Add this to UserController.java
@GetMapping
public ResponseEntity<?> getAllUsers() {
    List<AppUser> users = userRepository.findAll();
    
    // Return users without passwords
    List<Map<String, Object>> userDtos = users.stream()
        .map(user -> {
            Map<String, Object> dto = new HashMap<>();
            dto.put("id", user.getId());
            dto.put("username", user.getUsername());
            dto.put("email", user.getEmail());
            return dto;
        })
        .collect(Collectors.toList());
    
    return ResponseEntity.ok(userDtos);
}
}