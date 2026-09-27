package com.pokedex.backend.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;
@Entity
@Table(name = "users", uniqueConstraints = {
    @UniqueConstraint(columnNames = "username"), @UniqueConstraint(columnNames = "email")
}
)
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)Long id;
    @Column(nullable = false, length = 40)String username;
    @Column(nullable = false, length = 120)String email;
    @Column(nullable = false)String passwordHash;
    @Column(nullable = false)String role = "USER";
    @Column(nullable = false)LocalDateTime createdAt = LocalDateTime.now();
    public Long getId(){
        return id;
    }
    public String getUsername(){
        return username;
    }
    public void setUsername(String v){
        username = v;
    }
    public String getEmail(){
        return email;
    }
    public void setEmail(String v){
        email = v;
    }
    public String getPasswordHash(){
        return passwordHash;
    }
    public void setPasswordHash(String v){
        passwordHash = v;
    }
    public String getRole(){
        return role;
    }
    public LocalDateTime getCreatedAt(){
        return createdAt;
    }
}
