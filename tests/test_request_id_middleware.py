
import uuid

from fastapi.testclient import TestClient

from app.api.main import app


def test_health_endpoint_returns_valid_request_id():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None

    parsed_id = uuid.UUID(request_id)
    assert str(parsed_id) == request_id


def test_each_request_gets_a_unique_request_id():
    with TestClient(app) as client:
        first_response = client.get("/health")
        second_response = client.get("/health")

    first_id = first_response.headers["X-Request-ID"]
    second_id = second_response.headers["X-Request-ID"]

    assert first_id != second_id
