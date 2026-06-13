import logging

logger = logging.getLogger("app.log_utils")

_TRUNCATE_LENGTH = 200


def log_prompt(logger: logging.Logger, prompt: str, label: str = "prompt") -> None:
    logger.info("%s | length=%d", label, len(prompt))
    logger.debug("%s_full | length=%d content=%.200s...", label, len(prompt), prompt)


def log_response(logger: logging.Logger, response: str, label: str = "response") -> None:
    logger.info("%s | length=%d", label, len(response))
    logger.debug("%s_full | length=%d content=%.200s...", label, len(response), response)


def log_model_call(
    logger: logging.Logger,
    provider: str,
    model: str,
    duration_ms: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    logger.info(
        "model_call | provider=%s model=%s duration_ms=%.0f inputTokens=%d outputTokens=%d",
        provider, model, duration_ms, input_tokens, output_tokens,
    )


def log_tool_call(
    logger: logging.Logger,
    tool_name: str,
    duration_ms: float,
    args_length: int = 0,
    result_length: int = 0,
    status: str = "ok",
) -> None:
    logger.info(
        "tool_call | name=%s status=%s duration_ms=%.0f argsLength=%d resultLength=%d",
        tool_name, status, duration_ms, args_length, result_length,
    )
