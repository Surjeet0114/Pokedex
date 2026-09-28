from __future__ import annotations

import pytest

from app import create_app
from app.services import java_api, pokeapi


@pytest.fixture
def client():
    app = create_app()
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-session-secret",
        WTF_CSRF_ENABLED=False,
    )
    return app.test_client()


def sign_in(client):
    with client.session_transaction() as session:
        session["access_token"] = "test-token"
        session["user"] = {"username": "ash", "email": "ash@example.com"}


def sample_pokemon():
    return {
        "name": "Pikachu",
        "id": 25,
        "types": ["electric"],
        "height": 4,
        "weight": 60,
        "image_front": None,
        "image_back": None,
        "image_hd": None,
        "stats": {"hp": 35},
        "moves": [],
        "color": "yellow",
        "habitat": "forest",
        "evolution": [],
        "abilities": [],
        "cry": None,
    }


def test_home_renders_pokedex_and_stylesheet(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Every Pok\xc3\xa9mon has a story" in response.data
    assert b"style.css" in response.data
    assert b"Compare" in response.data
    stylesheet = client.get("/static/style.css")
    assert stylesheet.status_code == 200
    assert b"--red" in stylesheet.data


def test_forms_reject_requests_without_csrf_token():
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="csrf-test-secret", WTF_CSRF_ENABLED=True)

    response = app.test_client().post(
        "/login", data={"username": "ash", "password": "password123"}
    )

    assert response.status_code == 400


@pytest.mark.parametrize("path", ["/profile", "/favorites", "/history"])
def test_protected_pages_redirect_to_login(client, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_register_creates_session_and_redirects(client, monkeypatch):
    monkeypatch.setattr(
        java_api,
        "register",
        lambda username, email, password: {
            "token": "signed-token",
            "user": {"username": username, "email": email},
        },
    )

    response = client.post(
        "/register",
        data={"username": "ash", "email": "ash@example.com", "password": "password123"},
    )

    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session["access_token"] == "signed-token"
        assert session["user"]["username"] == "ash"


def test_register_shows_backend_error(client, monkeypatch):
    def reject_registration(*args):
        raise java_api.JavaApiError("Email already exists.", 400)

    monkeypatch.setattr(java_api, "register", reject_registration)
    response = client.post(
        "/register",
        data={"username": "ash", "email": "ash@example.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert b"Email already exists" in response.data


def test_login_and_logout(client, monkeypatch):
    monkeypatch.setattr(
        java_api,
        "login",
        lambda username, password: {
            "token": "signed-token",
            "user": {"username": username, "email": "ash@example.com"},
        },
    )
    response = client.post("/login", data={"username": "ash", "password": "password123"})
    assert response.status_code == 302

    response = client.post("/logout")
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert "access_token" not in session


def test_login_displays_invalid_credentials(client, monkeypatch):
    def reject_login(*args):
        raise java_api.JavaApiError("Invalid username or password.", 401)

    monkeypatch.setattr(java_api, "login", reject_login)
    response = client.post("/login", data={"username": "ash", "password": "wrong"})

    assert response.status_code == 401
    assert b"Invalid username or password" in response.data


def test_search_handles_blank_not_found_and_service_failure(client, monkeypatch):
    response = client.post("/search", data={"pokemon": " "})
    assert response.status_code == 400
    assert b"Enter a Pok\xc3\xa9mon" in response.data

    monkeypatch.setattr(pokeapi, "pokemon", lambda name: None)
    response = client.post("/search", data={"pokemon": "missingno"})
    assert response.status_code == 404
    assert b"No Pok\xc3\xa9mon found" in response.data

    def unavailable(name):
        raise pokeapi.PokeApiError("Pok\xc3\xa9API is currently unavailable.")

    monkeypatch.setattr(pokeapi, "pokemon", unavailable)
    response = client.post("/search", data={"pokemon": "pikachu"})
    assert response.status_code == 503
    assert b"currently unavailable" in response.data


def test_search_renders_details_and_records_history_for_signed_in_user(client, monkeypatch):
    sign_in(client)
    monkeypatch.setattr(pokeapi, "pokemon", lambda name: sample_pokemon())
    calls = []
    monkeypatch.setattr(java_api, "add_history", lambda pokemon: calls.append(pokemon))

    response = client.post("/search", data={"pokemon": "25"})

    assert response.status_code == 200
    assert b"Pikachu" in response.data
    assert b"Base stats" in response.data
    assert len(calls) == 1
    assert calls[0]["id"] == 25


def test_compare_renders_both_pokemon_and_handles_api_failure(client, monkeypatch):
    monkeypatch.setattr(pokeapi, "pokemon", lambda name: sample_pokemon())
    response = client.post(
        "/compare", data={"pokemon1": "pikachu", "pokemon2": "25"}
    )
    assert response.status_code == 200
    assert response.data.count(b"Pikachu") >= 2

    def unavailable(name):
        raise pokeapi.PokeApiError("Unavailable")

    monkeypatch.setattr(pokeapi, "pokemon", unavailable)
    response = client.post(
        "/compare", data={"pokemon1": "pikachu", "pokemon2": "25"}
    )
    assert response.status_code == 503
    assert b"Pok\xc3\xa9API is currently unavailable" in response.data


def test_favorites_history_and_profile_render_for_signed_in_user(client, monkeypatch):
    sign_in(client)
    monkeypatch.setattr(
        java_api, "favorites", lambda: [{"pokemonId": 25, "pokemonName": "Pikachu", "spriteUrl": None}]
    )
    monkeypatch.setattr(
        java_api,
        "history",
        lambda: [{"pokemonId": 25, "pokemonName": "Pikachu", "types": "electric", "searchedAt": "now"}],
    )
    monkeypatch.setattr(
        java_api,
        "me",
        lambda: {"username": "ash", "email": "ash@example.com", "role": "USER", "createdAt": "now"},
    )

    assert b"Pikachu" in client.get("/favorites").data
    assert b"Pikachu" in client.get("/history").data
    assert b"ash@example.com" in client.get("/profile").data


def test_favorite_add_remove_and_external_referrer_safety(client, monkeypatch):
    sign_in(client)
    calls = []
    monkeypatch.setattr(java_api, "add_favorite", lambda pokemon: calls.append(("add", pokemon)))
    monkeypatch.setattr(java_api, "remove_favorite", lambda pokemon_id: calls.append(("remove", pokemon_id)))

    response = client.post(
        "/favorites/25",
        data={"name": "Pikachu", "sprite": "sprite.png"},
        headers={"Referer": "http://localhost/favorites"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/favorites")
    assert calls[0][0] == "add"

    response = client.post(
        "/favorites/25",
        data={"action": "remove"},
        headers={"Referer": "https://attacker.example/"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert calls[1] == ("remove", 25)


def test_backend_unauthorized_response_expires_local_session(client, monkeypatch):
    sign_in(client)

    def expired_session():
        raise java_api.JavaApiError("Your session has expired. Please log in again.", 401)

    monkeypatch.setattr(java_api, "favorites", expired_session)
    response = client.get("/favorites")

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "access_token" not in session
