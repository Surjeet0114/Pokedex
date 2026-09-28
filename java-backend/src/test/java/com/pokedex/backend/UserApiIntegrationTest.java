package com.pokedex.backend;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.pokedex.backend.repository.FavoriteRepository;
import com.pokedex.backend.repository.SearchHistoryRepository;
import com.pokedex.backend.repository.UserRepository;
import com.pokedex.backend.security.JwtService;
import io.jsonwebtoken.ExpiredJwtException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest(
        properties = {
            "spring.datasource.url=jdbc:h2:mem:pokedex;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
            "spring.datasource.driver-class-name=org.h2.Driver",
            "spring.datasource.username=sa",
            "spring.datasource.password=",
            "spring.jpa.hibernate.ddl-auto=create-drop",
            "app.jwt.secret=integration-test-secret-with-at-least-32-bytes",
            "app.jwt.expiration-ms=3600000",
            "app.cors.origin=http://localhost:5000"
        })
@AutoConfigureMockMvc
class UserApiIntegrationTest {
    private static final String PASSWORD = "correct-horse-battery";

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @Autowired private UserRepository users;
    @Autowired private FavoriteRepository favorites;
    @Autowired private SearchHistoryRepository history;

    @BeforeEach
    void clearDatabase() {
        history.deleteAll();
        favorites.deleteAll();
        users.deleteAll();
    }

    @Test
    void registersUserHashesPasswordAndDoesNotReturnHash() throws Exception {
        mockMvc.perform(registerRequest("ash", "ash@example.com"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.user.username").value("ash"))
                .andExpect(jsonPath("$.user.passwordHash").doesNotExist());

        var user = users.findByUsername("ash").orElseThrow();
        org.assertj.core.api.Assertions.assertThat(user.getPasswordHash())
                .startsWith("$2")
                .isNotEqualTo(PASSWORD);
    }

    @Test
    void rejectsDuplicateUsernameAndEmail() throws Exception {
        mockMvc.perform(registerRequest("ash", "ash@example.com"))
                .andExpect(status().isCreated());

        mockMvc.perform(registerRequest("ash", "other@example.com"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.message").value("Username already exists."));

        mockMvc.perform(registerRequest("misty", "ASH@example.com"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.message").value("Email already exists."));
    }

    @Test
    void rejectsBcryptPasswordsThatWouldBeSilentlyTruncated() throws Exception {
        String longUtf8Password = "é".repeat(37);
        String request = """
                {"username":"ash","email":"ash@example.com","password":"%s"}
                """.formatted(longUtf8Password);

        mockMvc.perform(
                        post("/api/auth/register")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(request))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value(
                        "Password must be no more than 72 UTF-8 bytes."));
    }

    @Test
    void healthEndpointIsPublic() throws Exception {
        mockMvc.perform(get("/api/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"))
                .andExpect(jsonPath("$.service").value("pokedex-backend"));
    }

    @Test
    void loginRejectsInvalidCredentialsAndReturnsJwtForValidCredentials() throws Exception {
        mockMvc.perform(registerRequest("ash", "ash@example.com"))
                .andExpect(status().isCreated());

        mockMvc.perform(loginRequest("ash", "wrong-password"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.message").value("Invalid username or password."));

        mockMvc.perform(loginRequest("ash", PASSWORD))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.user.email").value("ash@example.com"));
    }

    @Test
    void protectsProfileAndRejectsMissingOrInvalidBearerTokens() throws Exception {
        mockMvc.perform(get("/api/users/me"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.message").value("Authentication required."));

        mockMvc.perform(get("/api/users/me").header("Authorization", "Bearer invalid"))
                .andExpect(status().isUnauthorized());

        String token = registerAndGetToken("ash", "ash@example.com");
        mockMvc.perform(get("/api/users/me").header("Authorization", "bEaReR " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("ash"));
    }

    @Test
    void rejectsExpiredJwtTokens() throws InterruptedException {
        JwtService shortLivedTokens =
                new JwtService("integration-test-secret-with-at-least-32-bytes", 1);
        String token = shortLivedTokens.generate("ash");
        Thread.sleep(10);

        assertThrows(ExpiredJwtException.class, () -> shortLivedTokens.username(token));
    }

    @Test
    void persistsAndReturnsUserOwnedFavoritesAndSearchHistory() throws Exception {
        String token = registerAndGetToken("ash", "ash@example.com");
        String authorization = "Bearer " + token;

        mockMvc.perform(
                        post("/api/users/history")
                                .header("Authorization", authorization)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"pokemonId":25,"pokemonName":"Pikachu","types":"electric"}
                                        """))
                .andExpect(status().isCreated());

        mockMvc.perform(get("/api/users/history").header("Authorization", authorization))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].pokemonId").value(25))
                .andExpect(jsonPath("$[0].pokemonName").value("Pikachu"))
                .andExpect(jsonPath("$[0].types").value("electric"));

        MvcResult favoriteResult = mockMvc.perform(
                        post("/api/users/favorites")
                                .header("Authorization", authorization)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {"pokemonId":25,"pokemonName":"Pikachu","spriteUrl":"https://example.test/pikachu.png"}
                                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.pokemonId").value(25))
                .andReturn();

        JsonNode favorite = objectMapper.readTree(
                favoriteResult.getResponse().getContentAsString());
        long favoriteId = favorite.get("id").asLong();

        mockMvc.perform(get("/api/users/favorites").header("Authorization", authorization))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(favoriteId))
                .andExpect(jsonPath("$[0].spriteUrl").value("https://example.test/pikachu.png"));

        String otherUserToken = registerAndGetToken("brock", "brock@example.com");
        mockMvc.perform(get("/api/users/favorites").header("Authorization", "Bearer " + otherUserToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isEmpty());

        mockMvc.perform(
                        delete("/api/users/favorites/25")
                                .header("Authorization", authorization))
                .andExpect(status().isNoContent());

        mockMvc.perform(get("/api/users/favorites").header("Authorization", authorization))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isEmpty());
    }

    private String registerAndGetToken(String username, String email) throws Exception {
        MvcResult result = mockMvc.perform(registerRequest(username, email))
                .andExpect(status().isCreated())
                .andReturn();
        return objectMapper.readTree(result.getResponse().getContentAsString())
                .get("token")
                .asText();
    }

    private static org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder
            registerRequest(String username, String email) {
        return post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"username":"%s","email":"%s","password":"%s"}
                        """.formatted(username, email, PASSWORD));
    }

    private static org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder
            loginRequest(String username, String password) {
        return post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"username":"%s","password":"%s"}
                        """.formatted(username, password));
    }
}
