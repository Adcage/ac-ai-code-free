from fastapi.testclient import TestClient

from app.main import create_app


def test_stream_code_generation_returns_sse_events():
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/agent/code-generation/stream",
        json={
            "agentRunId": "1",
            "appId": 2,
            "sessionId": 3,
            "userId": 4,
            "prompt": "create app",
            "codeGenType": "vue_project",
            "workspacePath": "E:/tmp/workspace",
        },
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "event: agent_start" in response.text
    assert "event: done" in response.text
