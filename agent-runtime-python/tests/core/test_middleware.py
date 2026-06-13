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


def test_readiness_endpoint(client: TestClient):
    response = client.get("/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "checks" in data.get("data", {})


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


def test_nonexistent_route_returns_404(client: TestClient):
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404


def test_unhandled_error_returns_400():
    from fastapi import Request
    from app.core.error_codes import AgentErrorCode
    from app.core.exceptions import AgentRuntimeError

    app = create_app()

    @app.get("/test-error")
    async def trigger_error(request: Request):
        raise AgentRuntimeError("test error", code=AgentErrorCode.INTERNAL_ERROR, status_code=400)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-error")
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == AgentErrorCode.INTERNAL_ERROR
    assert data["message"] == "test error"
    assert data["request_id"] is not None
