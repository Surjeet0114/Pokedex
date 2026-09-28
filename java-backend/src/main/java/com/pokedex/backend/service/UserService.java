package com.pokedex.backend.service;

import com.pokedex.backend.dto.AuthResponse;
import com.pokedex.backend.dto.FavoriteRequest;
import com.pokedex.backend.dto.FavoriteResponse;
import com.pokedex.backend.dto.HistoryRequest;
import com.pokedex.backend.dto.HistoryResponse;
import com.pokedex.backend.dto.LoginRequest;
import com.pokedex.backend.dto.RegisterRequest;
import com.pokedex.backend.dto.UserResponse;
import com.pokedex.backend.exception.DuplicateResourceException;
import com.pokedex.backend.model.Favorite;
import com.pokedex.backend.model.SearchHistory;
import com.pokedex.backend.model.User;
import com.pokedex.backend.repository.FavoriteRepository;
import com.pokedex.backend.repository.SearchHistoryRepository;
import com.pokedex.backend.repository.UserRepository;
import com.pokedex.backend.security.JwtService;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserService {
    private static final int MAX_BCRYPT_PASSWORD_BYTES = 72;

    private final UserRepository users;
    private final SearchHistoryRepository history;
    private final FavoriteRepository favorites;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public UserService(
            UserRepository users,
            SearchHistoryRepository history,
            FavoriteRepository favorites,
            PasswordEncoder passwordEncoder,
            JwtService jwtService) {
        this.users = users;
        this.history = history;
        this.favorites = favorites;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        String username = request.username().trim();
        String email = request.email().trim().toLowerCase(Locale.ROOT);
        validatePasswordLength(request.password());

        if (users.existsByUsername(username)) {
            throw new DuplicateResourceException("Username already exists.");
        }
        if (users.existsByEmail(email)) {
            throw new DuplicateResourceException("Email already exists.");
        }

        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        users.save(user);

        return new AuthResponse(jwtService.generate(user.getUsername()), UserResponse.from(user));
    }

    @Transactional(readOnly = true)
    public AuthResponse login(LoginRequest request) {
        String username = request.username().trim();
        User user = users.findByUsername(username)
                .orElseThrow(() -> new BadCredentialsException("Invalid username or password."));

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new BadCredentialsException("Invalid username or password.");
        }

        return new AuthResponse(jwtService.generate(user.getUsername()), UserResponse.from(user));
    }

    @Transactional(readOnly = true)
    public UserResponse me(String username) {
        return UserResponse.from(currentUser(username));
    }

    @Transactional
    public void addHistory(String username, HistoryRequest request) {
        SearchHistory entry = new SearchHistory();
        entry.setUser(currentUser(username));
        entry.setPokemonId(request.pokemonId());
        entry.setPokemonName(request.pokemonName().trim());
        entry.setTypes(request.types() == null ? "" : request.types().trim());
        history.save(entry);
    }

    @Transactional(readOnly = true)
    public List<HistoryResponse> history(String username) {
        User user = currentUser(username);
        return history.findTop50ByUserOrderBySearchedAtDesc(user).stream()
                .map(HistoryResponse::from)
                .toList();
    }

    @Transactional
    public FavoriteResponse addFavorite(String username, FavoriteRequest request) {
        User user = currentUser(username);
        Favorite favorite = favorites.findByUserAndPokemonId(user, request.pokemonId())
                .orElseGet(() -> {
                    Favorite created = new Favorite();
                    created.setUser(user);
                    created.setPokemonId(request.pokemonId());
                    created.setPokemonName(request.pokemonName().trim());
                    created.setSpriteUrl(request.spriteUrl());
                    return favorites.save(created);
                });
        return FavoriteResponse.from(favorite);
    }

    @Transactional
    public void removeFavorite(String username, Integer pokemonId) {
        if (pokemonId == null || pokemonId <= 0) {
            throw new IllegalArgumentException("Pokédex number must be positive.");
        }
        User user = currentUser(username);
        favorites.findByUserAndPokemonId(user, pokemonId).ifPresent(favorites::delete);
    }

    @Transactional(readOnly = true)
    public List<FavoriteResponse> favorites(String username) {
        User user = currentUser(username);
        return favorites.findByUserOrderByCreatedAtDesc(user).stream()
                .map(FavoriteResponse::from)
                .toList();
    }

    private User currentUser(String username) {
        return users.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));
    }

    private void validatePasswordLength(String password) {
        int byteLength = password.getBytes(StandardCharsets.UTF_8).length;
        if (byteLength > MAX_BCRYPT_PASSWORD_BYTES) {
            throw new IllegalArgumentException("Password must be no more than 72 UTF-8 bytes.");
        }
    }
}
