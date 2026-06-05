import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.events.agent_event import AgentEvent

router = APIRouter(prefix="/agent/code-generation", tags=["code-generation"])


class CodeGenerationRequest(BaseModel):
    agentRunId: str
    appId: int
    sessionId: int
    userId: int
    prompt: str
    codeGenType: str
    workspacePath: str | None = None
    modelConfigId: int | None = None
    configVersion: int | None = None


def validate_workspace_path(workspace_path: str | None) -> Path | None:
    if not workspace_path:
        return None
    resolved = Path(workspace_path).resolve()
    if ".." in workspace_path:
        raise ValueError(f"工作区路径不允许包含 .. : {workspace_path}")
    if resolved.is_absolute() and not str(resolved).startswith(str(Path.cwd())):
        raise ValueError(f"工作区路径必须在项目目录内: {workspace_path}")
    return resolved


async def event_stream(request: CodeGenerationRequest) -> AsyncIterator[str]:
    workspace = validate_workspace_path(request.workspacePath)
    if workspace:
        workspace.mkdir(parents=True, exist_ok=True)

    events = [
        AgentEvent(
            agentRunId=request.agentRunId,
            seq=1,
            eventType="agent_start",
            data={"runtime": "python-langgraph", "workspace": str(workspace) if workspace else None},
        ),
        AgentEvent(
            agentRunId=request.agentRunId,
            seq=2,
            eventType="done",
            data={"message": "Python Agent Runtime skeleton completed"},
        ),
    ]
    for event in events:
        yield f"event: {event.eventType}\n"
        yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"


@router.post("/stream")
async def stream_code_generation(request: CodeGenerationRequest) -> StreamingResponse:
    return StreamingResponse(event_stream(request), media_type="text/event-stream")
