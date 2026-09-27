package com.pokedex.backend.dto;
import jakarta.validation.constraints.*;
public record LoginRequest(@NotBlank String username, @NotBlank String password){
}
