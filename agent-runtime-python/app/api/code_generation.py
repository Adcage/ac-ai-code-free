import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.exceptions import AgentRuntimeError
from app.core.logging import get_logger
from app.core.response import success
from app.events.agent_event import AgentEvent

logger = get_logger("app.api.code_generation")

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


async def event_stream(request: CodeGenerationRequest, request_id: str) -> AsyncIterator[str]:
    logger.info(
        "agent_run_id=%s request_id=%s appId=%s codeGenType=%s prompt_len=%d",
        request.agentRunId,
        request_id,
        request.appId,
        request.codeGenType,
        len(request.prompt),
    )

    events = [
        AgentEvent(
            agentRunId=request.agentRunId,
            seq=1,
            eventType="agent_start",
            data={"runtime": "python-langgraph", "request_id": request_id},
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

    logger.info("agent_run_id=%s request_id=%s stream completed", request.agentRunId, request_id)


@router.post("/stream")
async def stream_code_generation(request: CodeGenerationRequest, http_request: Request) -> StreamingResponse:
    request_id = getattr(http_request.state, "request_id", "unknown")
    http_request.headers.get("X-Agent-Run-ID")

    return StreamingResponse(event_stream(request, request_id), media_type="text/event-stream")


@router.post("/submit")
async def submit_code_generation(request: CodeGenerationRequest, http_request: Request) -> dict:
    request_id = getattr(http_request.state, "request_id", "unknown")
    logger.info(
        "agent_run_id=%s request_id=%s appId=%s codeGenType=%s submit accepted",
        request.agentRunId,
        request_id,
        request.appId,
        request.codeGenType,
    )
    return success(data={"agentRunId": request.agentRunId, "status": "accepted"}, request=http_request)
