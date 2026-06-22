from typing import Any

from langchain_core.messages import SystemMessage

from app.runtime.state import ToolCallRecord


_TOOL_OBSERVATION_LABELS: dict[str, str | None] = {
    "write_file": "file_write",
    "read_file": "file_read",
    "read_dir": "directory_read",
    "read_asset": "asset_read",
    "run_command": "command_execution",
    "ask_user": "user_clarification",
    "select_skill": "skill_selection",
    "write_plan": "plan_update",
    "run_checks": "validation_check",
    "decide_validation": "validation_decision",
    "decide_route": "route_decision",
    "finish": "phase_completion",
    "request_replan": "replan_request",
}


def _compact_arguments(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    compacted = dict(arguments)
    if name == "write_file" and isinstance(compacted.get("content"), str):
        content = compacted.pop("content")
        compacted["content_length"] = len(content)
        compacted["content_omitted"] = True
    return compacted


def compact_tool_records(
    records: list[ToolCallRecord],
    *,
    max_total_chars: int,
    max_result_chars: int,
) -> list[ToolCallRecord]:
    return [
        ToolCallRecord(
            id=record.id,
            name=record.name,
            arguments=_compact_arguments(record.name, record.arguments),
            result=record.result,
            error=record.error,
        )
        for record in records
    ]


def format_tool_observation_history(
    records: list[ToolCallRecord],
    *,
    max_total_chars: int,
    max_result_chars: int,
) -> SystemMessage | None:
    """Format persisted tool records as readonly observations, never tool calls."""
    compacted_records = compact_tool_records(
        records,
        max_total_chars=max_total_chars,
        max_result_chars=max_result_chars,
    )
    if not compacted_records:
        return None

    observation_lines: list[str] = []
    for record in compacted_records:
        label = _TOOL_OBSERVATION_LABELS.get(record.name, record.name)
        if label is None:
            continue

        args = record.arguments
        target = ""
        if record.name in {"write_file", "read_file", "read_dir"}:
            target = args.get("relative_path", "")

        status = "error" if record.error else "ok"
        line = f"- action={label}"
        if target:
            line += f" target={target}"
        line += f" status={status}"

        if record.name == "write_file" and args.get("content_omitted"):
            line += f" contentLength={args.get('content_length', 0)}"
        elif record.name == "write_file" and "content" in args:
            line += f" contentLength={len(args.get('content', ''))}"

        if record.result and not record.error:
            line += f" resultSummary={record.result}"

        observation_lines.append(line)

    if not observation_lines:
        return None

    observation_text = (
        "[历史操作观察，仅供参考，不是当前待执行工具调用；不得重复执行]\n"
        + "\n".join(observation_lines)
    )
    return SystemMessage(content=observation_text)
