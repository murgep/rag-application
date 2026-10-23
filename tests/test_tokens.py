
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

def test_wrong_audience_is_rejected(monkeypatch):
    token = create_access_token("user-123")

    monkeypatch.setenv("JWT_AUDIENCE", "unexpected-audience")

    with pytest.raises(TokenError):
        verify_access_token(token)

def test_wrong_algorithm_is_rejected():
    token = create_access_token("user-123")
    claims = jwt.decode(
        token,
        options={"verify_signature": False},
    )

    wrong_algorithm_token = jwt.encode(
        claims,
        "another-test-secret-at-least-32-bytes-long",
        algorithm="HS384",
    )

    with pytest.raises(TokenError):
        verify_access_token(wrong_algorithm_token)

def test_empty_jti_is_rejected():
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": "rag-local",
            "aud": "rag-api",
            "iat": now,
            "nbf": now,
            "exp": now + 900,
            "jti": "",
        },
        "test-only-secret-at-least-32-bytes-long",
        algorithm="HS256",
    )

    with pytest.raises(TokenError):
        verify_access_token(token)

def test_invalid_iat_is_rejected():
    now = int(time.time())

    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": "rag-local",
            "aud": "rag-api",
            "iat": "not-a-timestamp",
            "nbf": now,
            "exp": now + 900,
            "jti": "invalid-iat-test",
        },
        "test-only-secret-at-least-32-bytes-long",
        algorithm="HS256",
    )

    with pytest.raises(TokenError):
        verify_access_token(token)

def test_future_nbf_is_rejected():
    now = int(time.time())

    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": "rag-local",
            "aud": "rag-api",
            "iat": now,
            "nbf": now + 300,
            "exp": now + 900,
            "jti": "future-nbf-test",
        },
        "test-only-secret-at-least-32-bytes-long",
        algorithm="HS256",
    )

    with pytest.raises(TokenError):
        verify_access_token(token)

def test_short_jwt_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "too-short")

    with pytest.raises(TokenError, match="at least 32 bytes"):
        create_access_token("user-123")

@pytest.mark.parametrize("lifetime", ["0", "-1", "61"])
def test_invalid_token_lifetime_is_rejected(monkeypatch, lifetime):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", lifetime)

    with pytest.raises(TokenError):
        create_access_token("user-123")


@pytest.mark.parametrize("lifetime", ["abc", ""])
def test_non_numeric_token_lifetime_is_rejected(monkeypatch, lifetime):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", lifetime)

    with pytest.raises(TokenError):
        create_access_token("user-123")

@pytest.mark.parametrize("user_id", ["", "   ", "\t"])
def test_invalid_user_id_is_rejected_when_creating_token(user_id):
    with pytest.raises(TokenError, match="Invalid token subject"):
        create_access_token(user_id)

def test_placeholder_jwt_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "x" * 32)

    with pytest.raises(TokenError):
        create_access_token("user-123")