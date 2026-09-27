package com.pokedex.backend.security;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
@Service public class JwtService {
    final SecretKey key;
    final long expiration;
    public JwtService(@Value("${app.jwt.secret}")String secret, @Value("${app.jwt.expiration-ms}")long exp){
        key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        expiration = exp;
    }
    public String generate(String username){
        Date n = new Date();
        return Jwts.builder().subject(username).issuedAt(n).expiration(new Date(n.getTime()+expiration)).signWith(key).compact();
    }
    public String username(String token){
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload().getSubject();
    }
}
