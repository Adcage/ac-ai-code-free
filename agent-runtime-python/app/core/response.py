from typing import Any

from fastapi import Request


def success(data: Any = None, message: str = "OK", code: int = 0, request: Request | None = None) -> dict:
    request_id = getattr(request.state, "request_id", None) if request else None
    return {"code": code, "message": message, "data": data, "request_id": request_id}
