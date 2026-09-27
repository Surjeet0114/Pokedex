package com.pokedex.backend.dto;
import jakarta.validation.constraints.*;
public record HistoryRequest(@NotNull Integer pokemonId, @NotBlank String pokemonName, String types){
}
