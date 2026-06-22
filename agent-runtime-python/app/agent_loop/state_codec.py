import json
import logging

from app.agent_loop.state_v2 import (
    WorkflowState,
    WorkflowStateEnvelope,
)
from app.core.error_codes import AgentErrorCode
from app.core.exceptions import AgentRuntimeError

logger = logging.getLogger("app.agent_loop.state_codec")

_SENSITIVE_KEYS = frozenset(
    {"apiKey", "authorization", "secret", "token", "password", "credential"}
)


def _strip_sensitive_from_dict(data: dict) -> dict:
    result = {}
    for key, value in data.items():
        if key in _SENSITIVE_KEYS or key.lower() in {k.lower() for k in _SENSITIVE_KEYS}:
            continue
        elif isinstance(value, dict):
            result[key] = _strip_sensitive_from_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _strip_sensitive_from_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def _strip_file_contents_from_tool_calls(data: dict) -> dict:
    if "executed_tool_calls" in data and isinstance(data["executed_tool_calls"], list):
        cleaned_calls = []
        for call in data["executed_tool_calls"]:
            if not isinstance(call, dict):
                cleaned_calls.append(call)
                continue
            call = dict(call)
            args = call.get("arguments")
            if isinstance(args, dict) and call.get("name") == "write_file":
                args = dict(args)
                if "content" in args:
                    content = args.pop("content")
                    args["content_length"] = len(content) if isinstance(content, str) else 0
                    args["content_omitted"] = True
                call["arguments"] = args
            cleaned_calls.append(call)
        data = {**data, "executed_tool_calls": cleaned_calls}
    return data


def sanitize_persisted_state(envelope: WorkflowStateEnvelope) -> WorkflowStateEnvelope:
    data = envelope.workflow.model_dump()
    data = _strip_sensitive_from_dict(data)
    data = _strip_file_contents_from_tool_calls(data)
    sanitized_workflow = WorkflowState.model_validate(data)
    return WorkflowStateEnvelope(
        schema_version=envelope.schema_version,
        workflow=sanitized_workflow,
    )


def encode_loop_state(envelope: WorkflowStateEnvelope) -> str:
    sanitized = sanitize_persisted_state(envelope)
    return sanitized.model_dump_json(exclude_none=False)


def decode_loop_state(raw: str | dict | None) -> WorkflowStateEnvelope:
    if raw is None or raw == "":
        return WorkflowStateEnvelope(
            workflow=WorkflowState(current_mode="route")
        )

    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            raise AgentRuntimeError(
                f"loopStateJson 不是合法 JSON: {e}",
                code=AgentErrorCode.STATE_ERROR,
            )
    elif isinstance(raw, dict):
        data = raw
    else:
        raise AgentRuntimeError(
            f"不支持的 loopStateJson 类型: {type(raw).__name__}",
            code=AgentErrorCode.STATE_ERROR,
        )

    version = data.get("schema_version")

    if version == 2:
        try:
            return WorkflowStateEnvelope.model_validate(data)
        except Exception as e:
            raise AgentRuntimeError(
                f"v2 状态校验失败: {e}",
                code=AgentErrorCode.STATE_ERROR,
            )

    if version is None:
        from app.agent_loop.legacy_state_adapter import adapt_legacy_state
        return adapt_legacy_state(data)

    raise AgentRuntimeError(
        f"未知的 loopStateJson schema_version={version}，无法恢复",
        code=AgentErrorCode.STATE_ERROR,
    )
