package com.pokedex.backend.model;
import jakarta.persistence.*;
import java.time.LocalDateTime;
@Entity
@Table(name = "favorites", uniqueConstraints = @UniqueConstraint(columnNames = {
    "user_id", "pokemonId"
}
))
public class Favorite {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)Long id;
    @ManyToOne(optional = false, fetch = FetchType.LAZY)User user;
    @Column(nullable = false)Integer pokemonId;
    @Column(nullable = false)String pokemonName;
    String spriteUrl;
    @Column(nullable = false)LocalDateTime createdAt = LocalDateTime.now();
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
    public String getSpriteUrl(){
        return spriteUrl;
    }
    public void setSpriteUrl(String v) {
    spriteUrl = v;
    }
    public LocalDateTime getCreatedAt(){
        return createdAt;
    }
}
