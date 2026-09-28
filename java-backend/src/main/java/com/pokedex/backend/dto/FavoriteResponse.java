package com.pokedex.backend.dto;

import com.pokedex.backend.model.Favorite;
import java.time.LocalDateTime;

public record FavoriteResponse(
        Long id,
        Integer pokemonId,
        String pokemonName,
        String spriteUrl,
        LocalDateTime createdAt) {

    public static FavoriteResponse from(Favorite favorite) {
        return new FavoriteResponse(
                favorite.getId(),
                favorite.getPokemonId(),
                favorite.getPokemonName(),
                favorite.getSpriteUrl(),
                favorite.getCreatedAt());
    }
}
