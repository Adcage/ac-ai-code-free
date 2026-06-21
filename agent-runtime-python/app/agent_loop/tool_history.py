import json
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
    "switch_mode": None,
}


def _truncate_middle(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    marker = f"\n... 已省略 {len(text)} 字符 ...\n"
    available = max(0, limit - len(marker))
    omitted = len(text) - available
    marker = f"\n... 已省略 {omitted} 字符 ...\n"
    available = max(0, limit - len(marker))
    head = available * 3 // 4
    tail = available - head
    return text[:head] + marker + text[-tail:] if tail else text[:head] + marker


def _compact_arguments(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    compacted = dict(arguments)
    if name == "write_file" and isinstance(compacted.get("content"), str):
        content = compacted.pop("content")
        compacted["content_length"] = len(content)
        compacted["content_omitted"] = True
    for key, value in list(compacted.items()):
        if isinstance(value, str) and len(value) > 2_000:
            compacted[key] = _truncate_middle(value, 2_000)
    return compacted


def compact_tool_records(
    records: list[ToolCallRecord],
    *,
    max_total_chars: int,
    max_result_chars: int,
) -> list[ToolCallRecord]:
    selected: list[ToolCallRecord] = []
    used = 0
    for record in reversed(records):
        arguments = _compact_arguments(record.name, record.arguments)
        arguments_size = len(json.dumps(arguments, ensure_ascii=False))
        remaining = max_total_chars - used
        if arguments_size >= remaining:
            continue
        result_limit = min(max_result_chars, remaining - arguments_size)
        result = _truncate_middle(record.result or "", result_limit)
        size = arguments_size + len(result)
        selected.append(
            ToolCallRecord(
                id=record.id,
                name=record.name,
                arguments=arguments,
                result=result,
                error=record.error,
            )
        )
        used += size
    selected.reverse()
    return selected


def format_tool_observation_history(
    records: list[ToolCallRecord],
    *,
    max_total_chars: int,
    max_result_chars: int,
) -> SystemMessage | None:
    """Format persisted tool records as readonly observations, never tool calls."""
    full_count = len(records)
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
            line += f" resultSummary={record.result[:200]}"

        observation_lines.append(line)

    if not observation_lines:
        return None

    if len(compacted_records) < full_count:
        skipped = full_count - len(compacted_records)
        observation_lines.insert(0, f"[省略 {skipped} 条较早的历史操作记录]")

    observation_text = (
        "[历史操作观察，仅供参考，不是当前待执行工具调用；不得重复执行]\n"
        + "\n".join(observation_lines)
    )
    return SystemMessage(content=observation_text)
