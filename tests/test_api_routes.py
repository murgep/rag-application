import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user_permissions,
    get_rag_pipeline,
)
from app.api.routes import health_router, router
from app.auth.authorization import UserPermissions


class FakeRAGPipeline:
    def __init__(self):
        self.calls = []

    def ask(self, question, top_k=3, similarity_threshold=0.60,
            department=None, request_id=None, departments=None):
        self.calls.append({
            "question": question,
            "departments": departments,
            "department": department,
            "request_id": request_id,
        })
        return {
            "answer": "This is a test answer.",
            "sources": [],
        }


class FailingRAGPipeline:
    def ask(self, **kwargs):
        raise RuntimeError("Sensitive internal database error")


class RAGPipelineWithSources:
    def ask(self, **kwargs):
        return {
            "answer": "Employees receive annual leave.",
            "sources": [
                {
                    "document_id": "doc-001",
                    "source": "employee_handbook.pdf",
                    "page_number": 4,
                    "similarity": 0.91,
                }
            ],
        }


def create_test_app(
    permissions=None,
    rag_pipeline=None,
    authenticate=True,
):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.include_router(health_router)

    if authenticate:
        if permissions is None:
            permissions = UserPermissions(
                user_id="test-user",
                email="test@example.com",
                roles=frozenset({"employee"}),
                departments=frozenset({"HR"}),
            )

        app.dependency_overrides[get_current_user_permissions] = (
            lambda: permissions
        )

    if rag_pipeline is not None:
        app.dependency_overrides[get_rag_pipeline] = lambda: rag_pipeline

    return app


def test_ask_endpoint_forwards_department():
    rag = FakeRAGPipeline()
    client = TestClient(create_test_app(rag_pipeline=rag))

    response = client.post(
        "/api/v1/ask",
        json={"question": "What is the leave policy?"},
    )

    assert response.status_code == 200
    assert rag.calls[0]["question"] == "What is the leave policy?"
    assert rag.calls[0]["departments"] == frozenset({"HR"})
    assert rag.calls[0]["department"] is None


def test_ask_endpoint_without_department_field_uses_authorized_departments():
    rag = FakeRAGPipeline()
    permissions = UserPermissions(
        user_id="user-2",
        email="user2@example.com",
        roles=frozenset({"employee"}),
        departments=frozenset({"Finance", "HR"}),
    )
    client = TestClient(
        create_test_app(permissions=permissions, rag_pipeline=rag)
    )

    response = client.post(
        "/api/v1/ask",
        json={"question": "What policies can I access?"},
    )

    assert response.status_code == 200
    assert rag.calls[0]["departments"] == frozenset({"Finance", "HR"})


def test_ask_endpoint_returns_safe_error_on_rag_failure():
    client = TestClient(
        create_test_app(rag_pipeline=FailingRAGPipeline())
    )

    response = client.post(
        "/api/v1/ask",
        json={"question": "Test failure handling"},
    )

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "Sensitive internal database error" not in response.text


def test_ask_endpoint_propagates_request_id():
    rag = FakeRAGPipeline()
    client = TestClient(create_test_app(rag_pipeline=rag))

    response = client.post(
        "/api/v1/ask",
        headers={"X-Request-ID": "test-request-123"},
        json={"question": "Test request ID"},
    )

    assert response.status_code == 200
    # The middleware generates the request ID; it does not trust the
    # caller-supplied header as the internal request ID.
    assert isinstance(rag.calls[0]["request_id"], str)
    assert rag.calls[0]["request_id"]


def test_ask_endpoint_returns_source_details():
    client = TestClient(
        create_test_app(rag_pipeline=RAGPipelineWithSources())
    )

    response = client.post(
        "/api/v1/ask",
        json={"question": "What is the leave policy?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Employees receive annual leave."
    assert body["sources"] == [
        {
            "document_id": "doc-001",
            "source": "employee_handbook.pdf",
            "page_number": 4,
            "similarity": 0.91,
        }
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"question": ""},
        {"question": "   "},
        {},
        {"question": "x" * 2001},
    ],
)
def test_ask_endpoint_rejects_invalid_question(payload):
    client = TestClient(create_test_app(rag_pipeline=FakeRAGPipeline()))

    response = client.post("/api/v1/ask", json=payload)

    assert response.status_code == 422


def test_ask_endpoint_rejects_client_supplied_department():
    client = TestClient(create_test_app(rag_pipeline=FakeRAGPipeline()))

    response = client.post(
        "/api/v1/ask",
        json={
            "question": "What is the leave policy?",
            "department": "Finance",
        },
    )

    assert response.status_code == 422


def test_ask_endpoint_rejects_user_without_department_access():
    permissions = UserPermissions(
        user_id="user-no-departments",
        email="no-departments@example.com",
        roles=frozenset({"employee"}),
        departments=frozenset(),
    )
    rag = FakeRAGPipeline()
    client = TestClient(
        create_test_app(permissions=permissions, rag_pipeline=rag)
    )

    response = client.post(
        "/api/v1/ask",
        json={"question": "Show me company policies"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "DEPARTMENT_ACCESS_DENIED"
    assert rag.calls == []


def test_ask_endpoint_requires_authentication_by_default():
    rag = FakeRAGPipeline()
    client = TestClient(
        create_test_app(rag_pipeline=rag, authenticate=False)
    )

    response = client.post(
        "/api/v1/ask",
        json={"question": "What is the leave policy?"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTHENTICATION_REQUIRED"
    assert rag.calls == []
