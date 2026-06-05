import json
from collections.abc import AsyncIterator

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
    modelConfigId: int | None = None
    configVersion: int | None = None


async def event_stream(request: CodeGenerationRequest) -> AsyncIterator[str]:
    events = [
        AgentEvent(
            agentRunId=request.agentRunId,
            seq=1,
            eventType="agent_start",
            data={"runtime": "python-langgraph"},
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
