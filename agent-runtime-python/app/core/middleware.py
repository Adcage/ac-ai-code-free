import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("app.middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        incoming_correlation = request.headers.get("X-Agent-Run-ID")
        request.state.request_id = request_id
        request.state.agent_run_id = incoming_correlation

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"

        if incoming_correlation:
            response.headers["X-Agent-Run-ID"] = incoming_correlation

        logger.info(
            "request_id=%s agent_run_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            incoming_correlation or "-",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response
