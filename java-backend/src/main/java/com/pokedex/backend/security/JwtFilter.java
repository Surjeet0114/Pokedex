package com.pokedex.backend.security;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.*;
import java.util.*;
@Component public class JwtFilter extends OncePerRequestFilter {
    final JwtService jwt;
    public JwtFilter(JwtService j){
        jwt = j;
    }
    protected void doFilterInternal(HttpServletRequest r, HttpServletResponse s, FilterChain c)
    throws ServletException, IOException {
        String h = r.getHeader("Authorization");
        if (h!=null&&h.startsWith("Bearer "))try {
            String u = jwt.username(h.substring(7));
            SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(u, null, List.of()));
        }
        catch(Exception ignored){
        }
        c.doFilter(r, s);
    }
}
