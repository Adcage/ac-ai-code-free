import asyncio
from grpc import aio

from app.core.config import settings

_channel: aio.Channel | None = None
_channel_loop: asyncio.AbstractEventLoop | None = None


async def get_channel() -> aio.Channel:
    global _channel, _channel_loop
    current_loop = asyncio.get_running_loop()
    if _channel is None or _channel_loop is None or _channel_loop is not current_loop or _channel_loop.is_closed():
        _channel = aio.insecure_channel(settings.java_grpc_target)
        _channel_loop = current_loop
    return _channel


def get_internal_metadata() -> tuple[tuple[str, str], ...] | None:
    if not settings.agent_internal_secret:
        return None
    return (("x-internal-secret", settings.agent_internal_secret),)


async def close_channel():
    global _channel, _channel_loop
    if _channel is not None:
        await _channel.close()
        _channel = None
        _channel_loop = None
