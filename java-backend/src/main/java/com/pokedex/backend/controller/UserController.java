package com.pokedex.backend.controller;
import com.pokedex.backend.dto.*;
import com.pokedex.backend.service.UserService;
import jakarta.validation.Valid;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import java.util.*;
@RestController
@RequestMapping("/api/users")
public class UserController {
    final UserService users;
    public UserController(UserService u){
        users = u;
    }
    private String username(){
        return SecurityContextHolder.getContext().getAuthentication().getName();
    }
    @GetMapping("/me")
    public UserResponse me(){
        return users.me(username());
    }
    @PostMapping("/history")
    public Map<String, String> addHistory(@Valid @RequestBody HistoryRequest r){
        users.addHistory(username(), r);
        return Map.of("message", "History saved");
    }
    @GetMapping("/history")
    public List<Map<String, Object>> history(){
        return users.history(username());
    }
    @PostMapping("/favorites")
    public Map<String, String> addFavorite(@Valid @RequestBody FavoriteRequest r){
        users.addFavorite(username(), r);
        return Map.of("message", "Favorite saved");
    }
    @GetMapping("/favorites")
    public List<Map<String, Object>> favorites(){
        return users.favorites(username());
    }
    @DeleteMapping("/favorites/{pokemonId}")
    public Map<String, String> remove(@PathVariable Integer pokemonId){
        users.removeFavorite(username(), pokemonId);
        return Map.of("message", "Favorite removed");
    }
}
