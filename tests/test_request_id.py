
import uuid

from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health_endpoint_returns_request_id():
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers.get("x-request-id")
    assert request_id is not None

    # Verify that the request ID is a valid UUID.
    uuid.UUID(request_id)


def test_each_request_gets_a_unique_request_id():
    first_response = client.get("/health")
    second_response = client.get("/health")

    first_id = first_response.headers["x-request-id"]
    second_id = second_response.headers["x-request-id"]

    assert first_id != second_id
