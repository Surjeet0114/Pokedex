package com.pokedex.backend.controller;

import com.pokedex.backend.dto.FavoriteRequest;
import com.pokedex.backend.dto.FavoriteResponse;
import com.pokedex.backend.dto.HistoryRequest;
import com.pokedex.backend.dto.HistoryResponse;
import com.pokedex.backend.dto.MessageResponse;
import com.pokedex.backend.dto.UserResponse;
import com.pokedex.backend.service.UserService;
import jakarta.validation.Valid;
import java.security.Principal;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserService users;

    public UserController(UserService users) {
        this.users = users;
    }

    @GetMapping("/me")
    public UserResponse me(Principal principal) {
        return users.me(principal.getName());
    }

    @PostMapping("/history")
    public ResponseEntity<MessageResponse> addHistory(
            Principal principal, @Valid @RequestBody HistoryRequest request) {
        users.addHistory(principal.getName(), request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new MessageResponse("History saved."));
    }

    @GetMapping("/history")
    public List<HistoryResponse> history(Principal principal) {
        return users.history(principal.getName());
    }

    @PostMapping("/favorites")
    public FavoriteResponse addFavorite(
            Principal principal, @Valid @RequestBody FavoriteRequest request) {
        return users.addFavorite(principal.getName(), request);
    }

    @GetMapping("/favorites")
    public List<FavoriteResponse> favorites(Principal principal) {
        return users.favorites(principal.getName());
    }

    @DeleteMapping("/favorites/{pokemonId}")
    public ResponseEntity<Void> removeFavorite(Principal principal, @PathVariable int pokemonId) {
        users.removeFavorite(principal.getName(), pokemonId);
        return ResponseEntity.noContent().build();
    }
}
