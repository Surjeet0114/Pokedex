package com.pokedex.backend.service;
import com.pokedex.backend.dto.*;
import com.pokedex.backend.model.*;
import com.pokedex.backend.repository.*;
import com.pokedex.backend.security.JwtService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import java.util.*;
@Service public class UserService {
    private final UserRepository users;
    private final SearchHistoryRepository history;
    private final FavoriteRepository favorites;
    private final PasswordEncoder encoder;
    private final JwtService jwt;
    public UserService(UserRepository u, SearchHistoryRepository h, FavoriteRepository f, PasswordEncoder e, JwtService j){
        users = u;
        history = h;
        favorites = f;
        encoder = e;
        jwt = j;
    }
    public AuthResponse register(RegisterRequest r){
        if (users.existsByUsername(r.username()))
        throw new IllegalArgumentException("Username already exists.");
        if (users.existsByEmail(r.email()))
        throw new IllegalArgumentException("Email already exists.");
        User u = new User();
        u.setUsername(r.username().trim());
        u.setEmail(r.email().trim().toLowerCase());
        u.setPasswordHash(encoder.encode(r.password()));
        users.save(u);
        return new AuthResponse(jwt.generate(u.getUsername()), UserResponse.from(u));
    }
    public AuthResponse login(LoginRequest r){
        User u = users.findByUsername(r.username()).orElseThrow(()->new IllegalArgumentException("Invalid username or password."));
        if (!encoder.matches(r.password(), u.getPasswordHash()))
        throw new IllegalArgumentException("Invalid username or password.");
        return new AuthResponse(jwt.generate(u.getUsername()), UserResponse.from(u));
    }
    public User current(String username){
        return users.findByUsername(username).orElseThrow(()->new IllegalArgumentException("User not found."));
    }
    public UserResponse me(String username){
        return UserResponse.from(current(username));
    }
    public void addHistory(String username, HistoryRequest r){
        User u = current(username);
        SearchHistory h = new SearchHistory();
        h.setUser(u);
        h.setPokemonId(r.pokemonId());
        h.setPokemonName(r.pokemonName());
        h.setTypes(r.types());
        history.save(h);
    }
    public List<Map<String, Object>> history(String username) {
        User user = current(username);

        return history.findTop50ByUserOrderBySearchedAtDesc(user)
                .stream()
                .map(h -> {
                    Map<String, Object> result = new HashMap<>();

                    result.put("id", h.getId());
                    result.put("pokemonId", h.getPokemonId());
                    result.put("pokemonName", h.getPokemonName());
                    result.put("types", Objects.toString(h.getTypes(), ""));
                    result.put("searchedAt", h.getSearchedAt().toString());

                    return result;
                })
                .toList();
    }
    public void addFavorite(String username, FavoriteRequest r){
        User u = current(username);
        if (favorites.findByUserAndPokemonId(u, r.pokemonId()).isPresent())return;
        Favorite f = new Favorite();
        f.setUser(u);
        f.setPokemonId(r.pokemonId());
        f.setPokemonName(r.pokemonName());
        f.setSpriteUrl(r.spriteUrl());
        favorites.save(f);
    }
    public void removeFavorite(String username, Integer id){
        favorites.findByUserAndPokemonId(current(username), id).ifPresent(favorites::delete);
    }
}
