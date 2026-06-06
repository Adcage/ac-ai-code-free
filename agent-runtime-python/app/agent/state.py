from typing import TypedDict

from app.events.agent_event import AgentEvent
from app.schemas.code_generation import CodeGenerationRequest


class AgentState(TypedDict):
    request: CodeGenerationRequest
    events: list[AgentEvent]
