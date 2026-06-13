import logging
from collections.abc import AsyncIterator
from collections.abc import Callable
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from app.agent.graph import build_graph
from app.events.agent_event import AgentEvent
from app.grpc_client.platform_client import GrpcPlatformClient
from app.grpc_client.tool_client import GrpcToolClient
from app.schemas.code_generation import CodeGenerationRequest
from app.services.chat_model_factory import ChatModelFactory
from app.services.model_config_client import ModelConfigClient
from app.services.prompt_builder import PromptBuilder

logger = logging.getLogger("app.services.agent_service")

ToolClientFactory = Callable[[CodeGenerationRequest], Any | None]
PlatformClientFactory = Callable[[], Any]


class AgentService:
    def __init__(
        self,
        model_config_client: ModelConfigClient,
        chat_model_factory: ChatModelFactory,
        prompt_builder: PromptBuilder,
        tool_client_factory: ToolClientFactory | None = None,
        platform_client_factory: PlatformClientFactory | None = None,
    ):
        self.model_config_client = model_config_client
        self.chat_model_factory = chat_model_factory
        self.prompt_builder = prompt_builder
        self.tool_client_factory = tool_client_factory or (
            lambda request: GrpcToolClient(request.appId, request.codeGenType)
        )
        self.platform_client_factory = platform_client_factory or GrpcPlatformClient
        self.graph = build_graph()

    async def _resolve_chat_model(
        self,
        request: CodeGenerationRequest,
        platform_client: Any,
    ) -> tuple[dict | None, BaseChatModel | None]:
        if request.modelConfigId is None:
            return None, None
        try:
            config = await platform_client.get_model_config(request.modelConfigId, request.configVersion or 0)
            return config, self.chat_model_factory.create(config)
        except Exception as e:
            logger.warning("gRPC get_model_config failed, falling back to HTTP: %s", e)
            config = await self.model_config_client.get_runtime_config(
                request.modelConfigId,
                request.configVersion or 0,
            )
            return config, self.chat_model_factory.create(config)

    async def stream(self, request: CodeGenerationRequest) -> AsyncIterator[AgentEvent]:
        start = AgentEvent(agentRunId=request.agentRunId, seq=1, eventType="agent_start", data={"runtime": "python-langgraph"})
        yield start

        grpc_platform_client = self.platform_client_factory()
        model_config, chat_model = await self._resolve_chat_model(request, grpc_platform_client)
        grpc_tool_client = self.tool_client_factory(request)

        result = await self.graph.ainvoke({
            "request": request,
            "events": [start],
            "model_config": model_config,
            "chat_model": chat_model,
            "generated_content": None,
            "error": None,
            "grpc_tool_client": grpc_tool_client,
            "grpc_platform_client": grpc_platform_client,
        })
        for event in result["events"][1:]:
            yield event
