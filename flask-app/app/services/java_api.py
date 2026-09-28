from __future__ import annotations

from typing import Any

import requests
from flask import current_app, session


class JavaApiError(Exception):
    """A safe, user-facing error returned by the Java API client."""

    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


def _request(method: str, path: str, **kwargs: Any) -> Any:
    url = current_app.config["JAVA_API_URL"].rstrip("/") + path
    headers = dict(kwargs.pop("headers", {}))
    token = session.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(method, url, headers=headers, timeout=8, **kwargs)
    except requests.RequestException as error:
        raise JavaApiError("Java backend is unavailable.") from error

    try:
        payload = response.json() if response.content else {}
    except ValueError:
        payload = {}

    if response.status_code >= 400:
        detail = payload.get("message") if isinstance(payload, dict) else None
        if response.status_code == 401 and not path.startswith("/api/auth/"):
            session.clear()
            detail = "Your session has expired. Please log in again."

        # Keep infrastructure failures generic; API validation messages remain
        # useful to the person filling out the form.
        status_code = response.status_code
        if status_code >= 500:
            status_code = 503
            detail = "Java backend is unavailable."
        raise JavaApiError(detail or "Request failed. Please try again.", status_code)

    return payload


def register(username: str, email: str, password: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )


def login(username: str, password: str) -> dict[str, Any]:
    return _request(
        "POST", "/api/auth/login", json={"username": username, "password": password}
    )


def me() -> dict[str, Any]:
    return _request("GET", "/api/users/me")


def add_history(pokemon: dict[str, Any]) -> dict[str, Any]:
    return _request(
        "POST",
        "/api/users/history",
        json={
            "pokemonId": pokemon["id"],
            "pokemonName": pokemon["name"],
            "types": ",".join(pokemon["types"]),
        },
    )


def history() -> list[dict[str, Any]]:
    return _request("GET", "/api/users/history")


def favorites() -> list[dict[str, Any]]:
    return _request("GET", "/api/users/favorites")


def add_favorite(pokemon: dict[str, Any]) -> dict[str, Any]:
    return _request(
        "POST",
        "/api/users/favorites",
        json={
            "pokemonId": pokemon["id"],
            "pokemonName": pokemon["name"],
            "spriteUrl": pokemon.get("image_front"),
        },
    )


def remove_favorite(pokemon_id: int) -> dict[str, Any]:
    return _request("DELETE", f"/api/users/favorites/{pokemon_id}")
