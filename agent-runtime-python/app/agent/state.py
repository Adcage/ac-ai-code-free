from typing import TypedDict

from langchain_core.language_models.chat_models import BaseChatModel

from app.events.agent_event import AgentEvent
from app.schemas.code_generation import CodeGenerationRequest


class AgentState(TypedDict):
    request: CodeGenerationRequest
    events: list[AgentEvent]
    chat_model: BaseChatModel | None
    generated_content: str | None
    error: str | None
