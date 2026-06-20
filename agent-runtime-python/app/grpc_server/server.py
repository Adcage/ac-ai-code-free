import logging
from concurrent import futures

from grpc import aio

from app.core.config import settings
from app.grpc import code_generation_pb2_grpc
from app.grpc_server.code_generation_servicer import CodeGenerationServicer
from app.grpc_server.interceptors import RequestLoggingInterceptor

logger = logging.getLogger("app.grpc_server")


async def create_grpc_server() -> aio.Server:
    servicer = CodeGenerationServicer()

    interceptors = [RequestLoggingInterceptor()]
    server = aio.server(futures.ThreadPoolExecutor(max_workers=10), interceptors=interceptors)
    code_generation_pb2_grpc.add_CodeGenerationServiceServicer_to_server(servicer, server)
    server.add_insecure_port(f"[::]:{settings.grpc_server_port}")
    logger.info("gRPC server listening on port %s", settings.grpc_server_port)
    return server
