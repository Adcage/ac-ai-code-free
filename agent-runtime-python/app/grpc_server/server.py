import logging
from concurrent import futures

from grpc import aio

from app.core.config import settings
from app.grpc import code_generation_pb2_grpc
from app.grpc_server.code_generation_servicer import CodeGenerationServicer
from app.services.agent_service import AgentService
from app.services.chat_model_factory import ChatModelFactory
from app.services.model_config_client import ModelConfigClient
from app.services.prompt_builder import PromptBuilder

logger = logging.getLogger("app.grpc_server")


async def create_grpc_server() -> aio.Server:
    model_config_client = ModelConfigClient(settings.java_platform_base_url, settings.agent_internal_secret)
    chat_model_factory = ChatModelFactory()
    prompt_builder = PromptBuilder()
    agent_service = AgentService(model_config_client, chat_model_factory, prompt_builder)

    servicer = CodeGenerationServicer(agent_service)

    server = aio.server(futures.ThreadPoolExecutor(max_workers=10))
    code_generation_pb2_grpc.add_CodeGenerationServiceServicer_to_server(servicer, server)
    server.add_insecure_port(f"[::]:{settings.grpc_server_port}")
    logger.info("gRPC server listening on port %s", settings.grpc_server_port)
    return server
