package com.pokedex.backend.exception;
import org.springframework.http.*;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import java.util.*;
@RestControllerAdvice public class ApiExceptionHandler {
    @ExceptionHandler(IllegalArgumentException.class)ResponseEntity<Map<String, String>> illegal(IllegalArgumentException e){
        return ResponseEntity.badRequest().body(Map.of("message", e.getMessage()));
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)ResponseEntity<Map<String, String>> validation(MethodArgumentNotValidException e){
        String m = e.getBindingResult().getFieldErrors().stream().findFirst().map(x->x.getField()+": "+x.getDefaultMessage()).orElse("Invalid request");
        return ResponseEntity.badRequest().body(Map.of("message", m));
    }
}
