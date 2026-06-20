import json
from typing import Any

from app.runtime.state import ToolCallRecord


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
