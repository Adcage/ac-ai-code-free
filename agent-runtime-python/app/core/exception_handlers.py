import json
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AgentRuntimeError
from app.core.logging import get_logger

logger = get_logger("app.exception_handlers")


async def agent_runtime_error_handler(request: Request, exc: AgentRuntimeError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning("BusinessError request_id=%s code=%s message=%s", request_id, exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": None, "request_id": request_id},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    errors = json.loads(json.dumps(exc.errors(), default=str))
    logger.warning("ValidationError request_id=%s errors=%s", request_id, errors)
    return JSONResponse(
        status_code=422,
        content={"code": 4220, "message": "Validation Error", "data": {"errors": errors}, "request_id": request_id},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled exception request_id=%s: %s", request_id, exc)
    return JSONResponse(
        status_code=500,
        content={"code": 5000, "message": "Internal Server Error", "data": None, "request_id": request_id},
    )
