from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.api.router import api_router
from app.core.config import settings
from app.core.exception_handlers import (
    agent_runtime_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.exceptions import AgentRuntimeError
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.response import success


def create_app() -> FastAPI:
    setup_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, debug=settings.debug)

    app.add_exception_handler(AgentRuntimeError, agent_runtime_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.add_middleware(RequestContextMiddleware)

    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health(request: Request) -> dict:
        return success(data={"status": "ok", "runtime": settings.agent_runtime_name}, request=request)

    @app.get("/health/warmup", tags=["health"])
    async def warmup(request: Request) -> dict:
        return success(data={"status": "warmed"}, request=request)

    return app


app = create_app()
