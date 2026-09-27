package com.pokedex.backend.dto;
import jakarta.validation.constraints.*;
public record FavoriteRequest(@NotNull Integer pokemonId, @NotBlank String pokemonName, String spriteUrl){
}
