package com.pokedex.backend.repository;

import com.pokedex.backend.model.SearchHistory;
import com.pokedex.backend.model.User;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SearchHistoryRepository extends JpaRepository<SearchHistory, Long> {
    List<SearchHistory> findTop50ByUserOrderBySearchedAtDesc(User user);
}
