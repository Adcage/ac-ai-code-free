from collections.abc import AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel

from app.agent.graph import build_graph
from app.events.agent_event import AgentEvent
from app.schemas.code_generation import CodeGenerationRequest
from app.services.chat_model_factory import ChatModelFactory
from app.services.model_config_client import ModelConfigClient
from app.services.prompt_builder import PromptBuilder


class AgentService:
    def __init__(
        self,
        model_config_client: ModelConfigClient,
        chat_model_factory: ChatModelFactory,
        prompt_builder: PromptBuilder,
    ):
        self.model_config_client = model_config_client
        self.chat_model_factory = chat_model_factory
        self.prompt_builder = prompt_builder
        self.graph = build_graph()

    async def _resolve_chat_model(self, request: CodeGenerationRequest) -> BaseChatModel | None:
        if request.modelConfigId is None:
            return None
        config = await self.model_config_client.get_runtime_config(
            request.modelConfigId,
            request.configVersion or 0,
        )
        return self.chat_model_factory.create(config)

    async def stream(self, request: CodeGenerationRequest) -> AsyncIterator[AgentEvent]:
        start = AgentEvent(agentRunId=request.agentRunId, seq=1, eventType="agent_start", data={"runtime": "python-langgraph"})
        yield start
        chat_model = await self._resolve_chat_model(request)
        result = await self.graph.ainvoke({
            "request": request,
            "events": [start],
            "chat_model": chat_model,
            "generated_content": None,
            "error": None,
        })
        for event in result["events"][1:]:
            yield event
