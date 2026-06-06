from pathlib import Path

import pytest

from app.schemas.code_generation import CodeGenerationRequest
from app.services.agent_service import AgentService


@pytest.mark.asyncio
async def test_agent_service_writes_minimal_vue_project(tmp_path: Path):
    service = AgentService()
    request = CodeGenerationRequest(
        agentRunId="1",
        appId=2,
        sessionId=3,
        userId=4,
        prompt="创建一个首页",
        codeGenType="vue_project",
        workspacePath=str(tmp_path),
    )

    events = [event async for event in service.stream(request)]

    event_types = [event.eventType for event in events]
    assert "agent_start" in event_types
    assert "tool_request" in event_types
    assert "tool_executed" in event_types
    assert "done" in event_types
    assert (tmp_path / "src" / "App.vue").exists()
