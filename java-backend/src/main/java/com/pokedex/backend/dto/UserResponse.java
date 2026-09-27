package com.pokedex.backend.dto;
import com.pokedex.backend.model.User;
import java.time.LocalDateTime;
public record UserResponse(Long id, String username, String email, String role, LocalDateTime createdAt){
    public static UserResponse from(User u){
        return new UserResponse(u.getId(), u.getUsername(), u.getEmail(), u.getRole(), u.getCreatedAt());
    }
}
