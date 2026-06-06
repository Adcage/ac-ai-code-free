from pathlib import Path

import pytest

from app.agent.graph import build_graph
from app.schemas.code_generation import CodeGenerationRequest


@pytest.mark.asyncio
async def test_graph_writes_app_vue_with_fake_model(tmp_path: Path):
    request = CodeGenerationRequest(
        agentRunId="1",
        appId=2,
        sessionId=3,
        userId=4,
        prompt="create app",
        codeGenType="vue_project",
        workspacePath=str(tmp_path),
    )
    graph = build_graph()
    result = await graph.ainvoke({"request": request, "events": []})

    assert (tmp_path / "src" / "App.vue").exists()
    assert result["events"]
