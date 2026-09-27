package com.pokedex.backend.repository;
import com.pokedex.backend.model.*;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.*;
public interface SearchHistoryRepository extends JpaRepository<SearchHistory, Long> {
    List<SearchHistory> findTop50ByUserOrderBySearchedAtDesc(User user);
}
