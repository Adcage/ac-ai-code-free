import asyncio
import logging

logger = logging.getLogger("app.grpc_client.retry")


async def retry_async(
    fn,
    max_retries: int = 2,
    delay_seconds: float = 1.0,
    retryable_exceptions: tuple = (Exception,),
    label: str = "",
):
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    "retry | label=%s attempt=%d/%d error=%s, retrying in %.1fs",
                    label, attempt + 1, max_retries, e, delay_seconds,
                )
                await asyncio.sleep(delay_seconds)
            else:
                logger.error(
                    "retry | label=%s attempt=%d/%d error=%s, giving up",
                    label, attempt + 1, max_retries, e,
                )
    raise last_exception
