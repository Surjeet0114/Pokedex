from __future__ import annotations

import pytest

from app import create_app
from app.services import java_api


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.payload = payload or {}
        self.content = b"{}"

    def json(self):
        return self.payload


def test_protected_calls_use_configured_backend_and_bearer_token(monkeypatch):
    app = create_app()
    app.config.update(JAVA_API_URL="http://java-api.test/", SECRET_KEY="api-test-secret")
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return FakeResponse(payload={"username": "ash"})

    monkeypatch.setattr(java_api.requests, "request", fake_request)
    with app.test_request_context("/"):
        from flask import session

        session["access_token"] = "signed-token"
        result = java_api.me()

    assert result == {"username": "ash"}
    assert calls[0][0:2] == ("GET", "http://java-api.test/api/users/me")
    assert calls[0][2]["headers"]["Authorization"] == "Bearer signed-token"


def test_expired_backend_token_clears_flask_session(monkeypatch):
    app = create_app()
    app.config.update(SECRET_KEY="api-test-secret")
    monkeypatch.setattr(
        java_api.requests,
        "request",
        lambda *args, **kwargs: FakeResponse(
            status_code=401, payload={"message": "Authentication required."}
        ),
    )

    with app.test_request_context("/"):
        from flask import session

        session["access_token"] = "expired-token"
        with pytest.raises(java_api.JavaApiError, match="session has expired"):
            java_api.me()
        assert "access_token" not in session


def test_backend_internal_errors_are_not_exposed_to_the_user(monkeypatch):
    app = create_app()
    app.config.update(SECRET_KEY="api-test-secret")
    monkeypatch.setattr(
        java_api.requests,
        "request",
        lambda *args, **kwargs: FakeResponse(
            status_code=500, payload={"message": "database password leaked"}
        ),
    )

    with app.test_request_context("/"):
        with pytest.raises(java_api.JavaApiError) as error:
            java_api.me()

    assert str(error.value) == "Java backend is unavailable."
    assert error.value.status_code == 503
