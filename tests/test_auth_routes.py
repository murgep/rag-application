from unittest.mock import MagicMock

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth_routes import auth_router
from app.auth.passwords import hash_password
from app.auth.tokens import verify_access_token


@pytest.fixture
def login_client(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LOCAL_AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "JWT_SECRET",
        "test-only-secret-at-least-32-bytes-long",
    )
    monkeypatch.setenv("JWT_ISSUER", "rag-local")
    monkeypatch.setenv("JWT_AUDIENCE", "rag-api")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", "15")

    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")

    return TestClient(app)


def make_database_connection(user):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = user
    return connection


def test_login_success_returns_access_token_and_expiry(
    login_client,
    monkeypatch,
):
    password = "correct-test-password"
    user_id = "hr-user"
    password_hash = hash_password(password)

    connection = make_database_connection(
        (user_id, password_hash, True)
    )

    monkeypatch.setattr(
        "app.api.auth_routes.get_connection",
        lambda: connection,
    )

    response = login_client.post(
        "/api/v1/auth/login",
        json={
            "email": " HR@EXAMPLE.COM ",
            "password": password,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert verify_access_token(body["access_token"]) == user_id

    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.assert_called_once()
    assert cursor.execute.call_args.args[1] == ("hr@example.com",)
    connection.close.assert_called_once()


def test_login_wrong_password_returns_generic_401(
    login_client,
    monkeypatch,
):
    connection = make_database_connection(
        ("hr-user", hash_password("correct-password"), True)
    )

    monkeypatch.setattr(
        "app.api.auth_routes.get_connection",
        lambda: connection,
    )

    response = login_client.post(
        "/api/v1/auth/login",
        json={
            "email": "hr@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_unknown_user_returns_generic_401(
    login_client,
    monkeypatch,
):
    connection = make_database_connection(None)

    monkeypatch.setattr(
        "app.api.auth_routes.get_connection",
        lambda: connection,
    )

    response = login_client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "some-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_database_failure_returns_safe_503(
    login_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.auth_routes.get_connection",
        MagicMock(
            side_effect=psycopg.OperationalError(
                "Internal database details"
            )
        ),
    )

    response = login_client.post(
        "/api/v1/auth/login",
        json={
            "email": "hr@example.com",
            "password": "some-password",
        },
    )

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "Authentication service is temporarily unavailable."
    )
    assert response.headers["retry-after"] == "5"
    assert "Internal database details" not in response.text


def test_login_missing_database_configuration_returns_safe_503(
    login_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.auth_routes.get_connection",
        MagicMock(
            side_effect=ValueError(
                "Missing database environment variables: DATABASE_PASSWORD"
            )
        ),
    )

    response = login_client.post(
        "/api/v1/auth/login",
        json={
            "email": "hr@example.com",
            "password": "some-password",
        },
    )

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "Authentication service is temporarily unavailable."
    )
    assert "DATABASE_PASSWORD" not in response.text