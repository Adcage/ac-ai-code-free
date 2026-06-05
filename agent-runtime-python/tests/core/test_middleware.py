from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


def test_create_app_returns_fastapi_instance():
    app = create_app()
    assert isinstance(app, FastAPI)


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "ok"
    assert data["data"]["runtime"] == "python-langgraph"
    assert data["request_id"] is not None


def test_warmup_endpoint(client: TestClient):
    response = client.get("/health/warmup")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "warmed"


def test_request_id_in_response_headers(client: TestClient):
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


def test_different_requests_get_different_request_ids(client: TestClient):
    response1 = client.get("/health")
    response2 = client.get("/health")
    assert response1.headers["X-Request-ID"] != response2.headers["X-Request-ID"]


def test_agent_run_id_header_passthrough(client: TestClient):
    response = client.get("/health", headers={"X-Agent-Run-ID": "run-123"})
    assert response.headers.get("X-Agent-Run-ID") == "run-123"


def test_validation_error_returns_422(client: TestClient):
    response = client.post("/api/v1/agent/code-generation/stream", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == 4220
    assert data["request_id"] is not None


def test_unhandled_error_returns_500():
    from fastapi import Request
    from app.core.exceptions import AgentRuntimeError
    from app.core.response import success

    app = create_app()

    @app.get("/test-error")
    async def trigger_error(request: Request):
        raise AgentRuntimeError("test error", code=9999, status_code=400)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-error")
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == 9999
    assert data["message"] == "test error"
    assert data["request_id"] is not None
