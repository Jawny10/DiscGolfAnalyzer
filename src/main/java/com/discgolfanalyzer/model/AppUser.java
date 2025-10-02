// src/main/java/com/discgolfanalyzer/model/AppUser.java (rename the file from User.java)
package com.discgolfanalyzer.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import lombok.Data;

@Entity
@Data
@jakarta.persistence.Table(name = "app_users") // Change the table name to avoid reserved keyword
public class AppUser {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String username;
    private String email;
    private String password;
}