package com.pokedex.backend.repository;

import com.pokedex.backend.model.Favorite;
import com.pokedex.backend.model.User;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FavoriteRepository extends JpaRepository<Favorite, Long> {
    List<Favorite> findByUserOrderByCreatedAtDesc(User user);

    Optional<Favorite> findByUserAndPokemonId(User user, Integer pokemonId);
}
