package com.pokedex.backend.dto;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public record FavoriteRequest(
        @NotNull @Positive Integer pokemonId,
        @NotBlank @Size(max = 80) String pokemonName,
        @Size(max = 2048) String spriteUrl) {
}
