package com.pokedex.backend.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;
@Entity
@Table(name = "search_history")
public class SearchHistory {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)Long id;
    @ManyToOne(optional = false, fetch = FetchType.LAZY)User user;
    @Column(nullable = false)Integer pokemonId;
    @Column(nullable = false)String pokemonName;
    String types;
    @Column(nullable = false)LocalDateTime searchedAt = LocalDateTime.now();
    public Long getId(){
        return id;
    }
    public User getUser(){
        return user;
    }
    public void setUser(User v){
        user = v;
    }
    public Integer getPokemonId(){
        return pokemonId;
    }
    public void setPokemonId(Integer v){
        pokemonId = v;
    }
    public String getPokemonName(){
        return pokemonName;
    }
    public void setPokemonName(String v){
        pokemonName = v;
    }
    public String getTypes(){
        return types;
    }
    public void setTypes(String v){
        types = v;
    }
    public LocalDateTime getSearchedAt(){
        return searchedAt;
    }
}
