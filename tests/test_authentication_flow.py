import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.dependencies import (
    get_current_user_permissions,
    get_rag_pipeline,
)
from app.api.routes import router
from app.auth.authorization import AuthorizationService, UserPermissions
from app.auth.tokens import create_access_token


class FakeRAGPipeline:
    def __init__(self):
        self.calls = []

    def ask(self, question, departments=None, request_id=None, **kwargs):
        self.calls.append(
            {
                "question": question,
                "departments": departments,
                "request_id": request_id,
            }
        )
        return {"answer": "Test answer", "sources": []}


@pytest.fixture
def auth_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LOCAL_AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "JWT_SECRET",
        "test-only-secret-at-least-32-bytes-long",
    )
    monkeypatch.setenv("JWT_ISSUER", "rag-local")
    monkeypatch.setenv("JWT_AUDIENCE", "rag-api")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", "15")


@pytest.fixture
def setup_client(monkeypatch, auth_environment):
    permissions = UserPermissions(
        user_id="hr-user",
        email="hr@example.com",
        roles=frozenset({"employee"}),
        departments=frozenset({"HR"}),
    )

    # Replace only the database-backed permission lookup.
    # JWT verification remains real.
    monkeypatch.setattr(
        AuthorizationService,
        "get_user_permissions",
        lambda self, user_id: (
            permissions
            if user_id == "hr-user"
            else pytest.fail("Unexpected user ID")
        ),
    )

    rag = FakeRAGPipeline()
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_rag_pipeline] = lambda: rag

    return TestClient(app), rag


def test_valid_jwt_loads_permissions_and_limits_rag_departments(setup_client):
    client, rag = setup_client
    token = create_access_token("hr-user")

    response = client.post(
        "/api/v1/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What is the HR policy?"},
    )

    assert response.status_code == 200
    assert rag.calls[0]["departments"] == frozenset({"HR"})


def test_missing_token_is_rejected(setup_client):
    client, rag = setup_client

    response = client.post(
        "/api/v1/ask",
        json={"question": "What is the HR policy?"},
    )

    assert response.status_code == 401
    assert rag.calls == []


def test_invalid_token_is_rejected(setup_client):
    client, rag = setup_client

    response = client.post(
        "/api/v1/ask",
        headers={"Authorization": "Bearer not-a-valid-token"},
        json={"question": "What is the HR policy?"},
    )

    assert response.status_code == 401
    assert rag.calls == []


def test_client_cannot_choose_finance_department(setup_client):
    client, rag = setup_client
    token = create_access_token("hr-user")

    response = client.post(
        "/api/v1/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What is the Finance policy?",
            "department": "Finance",
        },
    )

    assert response.status_code == 422
    assert rag.calls == []


def test_valid_token_for_user_with_no_departments_is_denied(
    monkeypatch,
    auth_environment,
):
    permissions = UserPermissions(
        user_id="unassigned-user",
        email="unassigned@example.com",
        roles=frozenset({"employee"}),
        departments=frozenset(),
    )

    monkeypatch.setattr(
        AuthorizationService,
        "get_user_permissions",
        lambda self, user_id: permissions,
    )

    rag = FakeRAGPipeline()
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_rag_pipeline] = lambda: rag
    client = TestClient(app)

    token = create_access_token("unassigned-user")
    response = client.post(
        "/api/v1/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "Show me company policies"},
    )

    assert response.status_code == 403
    assert rag.calls == []

def test_database_failure_during_authentication_returns_503(
    setup_client,
    monkeypatch,
):
    client, rag = setup_client
    token = create_access_token("hr-user")

    def fail_permission_lookup(self, user_id):
        raise psycopg.OperationalError("Internal database details")

    monkeypatch.setattr(
        AuthorizationService,
        "get_user_permissions",
        fail_permission_lookup,
    )

    response = client.post(
        "/api/v1/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What is the HR policy?"},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Internal database details" not in response.text
    assert rag.calls == []