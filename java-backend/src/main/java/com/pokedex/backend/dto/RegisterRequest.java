package com.pokedex.backend.dto;
import jakarta.validation.constraints.*;
public record RegisterRequest(@NotBlank
@Size(min = 3, max = 40)String username, @NotBlank
@Email String email, @NotBlank
@Size(min = 8, max = 100)String password){
}
