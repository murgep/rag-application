
import time

import jwt
import pytest

from app.auth.tokens import (
    TokenError,
    create_access_token,
    verify_access_token,
)


@pytest.fixture(autouse=True)
def local_auth_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LOCAL_AUTH_ENABLED", "true")
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-at-least-32-bytes-long")
    monkeypatch.setenv("JWT_ISSUER", "rag-local")
    monkeypatch.setenv("JWT_AUDIENCE", "rag-api")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", "15")


def test_valid_token_returns_user_id():
    token = create_access_token("user-123")

    assert verify_access_token(token) == "user-123"


def test_tampered_token_is_rejected():
    token = create_access_token("user-123")
    parts = token.split(".")
    parts[1] = parts[1][:-1] + ("A" if parts[1][-1] != "A" else "B")
    tampered = ".".join(parts)

    with pytest.raises(TokenError):
        verify_access_token(tampered)


def test_expired_token_is_rejected(monkeypatch):
    token = create_access_token("user-123")
    secret = "test-only-secret-at-least-32-bytes-long"
    now = int(time.time())

    expired = jwt.encode(
        {
            "sub": "user-123",
            "iss": "rag-local",
            "aud": "rag-api",
            "iat": now - 120,
            "nbf": now - 120,
            "exp": now - 60,
            "jti": "expired-test-token",
        },
        secret,
        algorithm="HS256",
    )

    with pytest.raises(TokenError):
        verify_access_token(expired)


def test_wrong_issuer_is_rejected():
    token = create_access_token("user-123")
    wrong_issuer = jwt.decode(
        token,
        options={"verify_signature": False},
    )
    wrong_issuer["iss"] = "unexpected-issuer"

    altered = jwt.encode(
        wrong_issuer,
        "test-only-secret-at-least-32-bytes-long",
        algorithm="HS256",
    )

    with pytest.raises(TokenError):
        verify_access_token(altered)


def test_local_auth_disabled_rejects_token_creation(monkeypatch):
    monkeypatch.setenv("LOCAL_AUTH_ENABLED", "false")

    with pytest.raises(TokenError):
        create_access_token("user-123")


def test_production_environment_rejects_token_creation(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(TokenError):
        create_access_token("user-123")
