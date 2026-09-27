package com.pokedex.backend.controller;
import com.pokedex.backend.dto.*;
import com.pokedex.backend.service.UserService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api/auth")
public class AuthController {
    final UserService users;
    public AuthController(UserService u){
        users = u;
    }
    @PostMapping("/register")
    public AuthResponse register(@Valid @RequestBody RegisterRequest r){
        return users.register(r);
    }
    @PostMapping("/login")
    public AuthResponse login(@Valid @RequestBody LoginRequest r){
        return users.login(r);
    }
}
