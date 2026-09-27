package com.pokedex.backend.repository;
import com.pokedex.backend.model.*;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.*;
public interface FavoriteRepository extends JpaRepository<Favorite, Long> {
    List<Favorite> findByUserOrderByCreatedAtDesc(User user);
    Optional<Favorite> findByUserAndPokemonId(User user, Integer pokemonId);
}
