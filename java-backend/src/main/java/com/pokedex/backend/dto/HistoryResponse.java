package com.pokedex.backend.dto;

import com.pokedex.backend.model.SearchHistory;
import java.time.LocalDateTime;

public record HistoryResponse(
        Long id,
        Integer pokemonId,
        String pokemonName,
        String types,
        LocalDateTime searchedAt) {

    public static HistoryResponse from(SearchHistory history) {
        return new HistoryResponse(
                history.getId(),
                history.getPokemonId(),
                history.getPokemonName(),
                history.getTypes() == null ? "" : history.getTypes(),
                history.getSearchedAt());
    }
}
