import logging
from typing import Any

from langchain_core.messages import SystemMessage

from app.runtime.state import ToolCallRecord

logger = logging.getLogger("app.agent_loop.tool_history")

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
_RETIRED_TOOLS = frozenset({"switch_mode", "compose_prompt"})

_DEFAULT_CONTENT_CHARS = 4000

_STAGE_TOOLS = frozenset({
    "submit_requirement_brief", "record_project_inspection", "choose_skill",
    "propose_design", "confirm_design", "write_implementation_plan",
    "decide_route", "decide_validation", "finish",
})


def _truncate_text(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit] + f"\n... [截断，原长度={len(text)}]"


def _format_tool_arguments(record: ToolCallRecord) -> str:
    """对阶段工具展示关键参数摘要，让模型能看到自己提交了什么内容。"""
    args = record.arguments or {}
    name = record.name

    if name == "submit_requirement_brief":
        parts = []
        if args.get("application_direction"):
            parts.append(f"方向={_truncate_text(str(args['application_direction']), 200)}")
        if args.get("target_users"):
            parts.append(f"目标用户={_truncate_text(str(args['target_users']), 200)}")
        if args.get("functional_scope"):
            parts.append(f"功能范围={_truncate_text(str(args['functional_scope']), 200)}")
        if not parts:
            return ""
        return "参数: " + "，".join(parts)

    elif name == "propose_design":
        parts = []
        for key, label in [("visual_direction", "视觉"), ("color_system", "配色"),
                           ("typography", "字体"), ("component_language", "组件")]:
            val = args.get(key, "")
            if val:
                parts.append(f"{label}={_truncate_text(str(val), 100)}")
        if not parts:
            return ""
        return "参数: " + "，".join(parts)

    elif name == "write_implementation_plan":
        tasks = args.get("tasks", [])
        parts = [f"tasks={len(tasks)} 个"]
        if tasks:
            goals = []
            for t in list(tasks)[:2]:
                g = t.get("goal", "") if isinstance(t, dict) else ""
                if g:
                    goals.append(_truncate_text(str(g), 100))
            if goals:
                parts.append("目标: " + "; ".join(goals))
        test_plan = args.get("test_plan", [])
        if test_plan:
            parts.append(f"test_plan={len(test_plan)} 项")
        return "参数: " + "，".join(parts)

    elif name == "confirm_design":
        msg_id = args.get("message_id", "")
        if msg_id:
            return f"参数: message_id={msg_id}"
        return ""

    elif name == "record_project_inspection":
        parts = []
        if args.get("decision"):
            parts.append(f"decision={args['decision']}")
        evidence = args.get("evidence_files", [])
        if evidence:
            parts.append(f"evidence_files={len(evidence)} 个")
        return "参数: " + "，".join(parts) if parts else ""

    elif name == "choose_skill":
        parts = []
        if args.get("skill_id"):
            parts.append(f"skill_id={args['skill_id']}")
        if args.get("reason"):
            parts.append(f"reason={_truncate_text(str(args['reason']), 100)}")
        return "参数: " + "，".join(parts) if parts else ""

    return ""


def _compact_arguments(
    name: str,
    arguments: dict[str, Any],
    *,
    max_result_chars: int,
) -> dict[str, Any]:
    compacted = dict(arguments)
    if name == "write_file" and isinstance(compacted.get("content"), str):
        content = compacted["content"]
        compacted["content"] = _truncate_text(content, max_result_chars)
        compacted["content_length"] = len(content)
        compacted["content_truncated"] = len(content) > max_result_chars > 0
    return compacted


def compact_tool_records(
    records: list[ToolCallRecord],
    *,
    max_total_chars: int,
    max_result_chars: int,
) -> list[ToolCallRecord]:
    compacted_records = [
        ToolCallRecord(
            id=record.id,
            name=record.name,
            arguments=_compact_arguments(
                record.name,
                record.arguments,
                max_result_chars=max_result_chars,
            ),
            result=(
                _truncate_text(str(record.result), max_result_chars)
                if isinstance(record.result, str)
                else record.result
            ),
            error=record.error,
        )
        for record in records
    ]
    if max_total_chars <= 0:
        return compacted_records

    total = 0
    kept: list[ToolCallRecord] = []
    for record in reversed(compacted_records):
        record_size = len(str(record.arguments)) + len(str(record.result or "")) + len(str(record.error or ""))
        if kept and total + record_size > max_total_chars:
            break
        kept.append(record)
        total += record_size
    return list(reversed(kept))


def _get_target(record: ToolCallRecord) -> str:
    if record.name in {"write_file", "read_file", "read_dir"}:
        return record.arguments.get("relative_path", "")
    return ""


def _format_record(
    record: ToolCallRecord,
    *,
    skip_content: bool = False,
    content_limit: int = _DEFAULT_CONTENT_CHARS,
) -> str:
    if record.name in _RETIRED_TOOLS:
        return ""
    label = _TOOL_OBSERVATION_LABELS.get(record.name, record.name)
    if label is None:
        return ""

    target = _get_target(record)
    status = "error" if record.error else "ok"

    lines: list[str] = []
    header = f"--- {label}"
    if target:
        header += f" [{target}]"
    header += f" ({status})"
    lines.append(header)

    # 对阶段工具展示关键参数摘要（Fix: 让模型能看到自己提交了什么内容）
    arg_preview = _format_tool_arguments(record)
    if arg_preview:
        lines.append(arg_preview)

    if record.name == "read_file" and record.result and not record.error:
        if skip_content:
            lines.append("[内容省略，后续有更新读取]")
        else:
            lines.append(_truncate_text(str(record.result), content_limit))

    elif record.name == "write_file" and not record.error:
        raw = record.arguments.get("content")
        if raw is not None:
            if skip_content:
                lines.append("[内容省略，后续有更新写入]")
            else:
                lines.append(_truncate_text(str(raw), content_limit))
        else:
            lines.append(f"[内容已压缩，长度={record.arguments.get('content_length', 0)} 字符]")

    elif record.name == "read_dir" and record.result and not record.error:
        lines.append(f"结果: {_truncate_text(str(record.result), min(content_limit, 4_000))}")

    elif record.result and not record.error and record.name not in {"read_file", "write_file", "read_dir"}:
        lines.append(f"结果: {_truncate_text(str(record.result), min(content_limit, 2_000))}")

    return "\n".join(lines)


def format_tool_observation_history(
    records: list[ToolCallRecord],
    *,
    max_total_chars: int,
    max_result_chars: int,
) -> SystemMessage | None:
    if not records:
        return None
    content_limit = max_result_chars if max_result_chars > 0 else _DEFAULT_CONTENT_CHARS

    # Find the latest write/read per file path (from newest to oldest)
    latest_write: dict[str, int] = {}
    latest_read: dict[str, int] = {}
    latest_stage_success: dict[str, int] = {}
    for i, record in enumerate(records):
        if record.name == "write_file" and not record.error:
            p = _get_target(record)
            if p:
                latest_write[p] = i
        elif record.name == "read_file" and not record.error:
            p = _get_target(record)
            if p:
                latest_read[p] = i
        elif record.name in _STAGE_TOOLS and not record.error:
            latest_stage_success[record.name] = i

    # First pass: build all blocks, tracking per-file content dedup
    raw_blocks: list[tuple[int, str]] = []  # (size, text)

    for idx, record in enumerate(records):
        if record.name in _RETIRED_TOOLS:
            continue
        label = _TOOL_OBSERVATION_LABELS.get(record.name, record.name)
        if label is None:
            continue

        target = _get_target(record)
        skip = False

        if record.name == "write_file" and target and target in latest_write:
            skip = idx != latest_write[target]
        elif record.name == "read_file" and target and target in latest_read:
            skip = idx != latest_read[target]
        elif record.name in _STAGE_TOOLS and record.name in latest_stage_success:
            skip = idx != latest_stage_success[record.name]

        block = _format_record(record, skip_content=skip, content_limit=content_limit)
        if block:
            raw_blocks.append((len(block), block))

    if not raw_blocks:
        return None

    # Total up, truncate oldest first if over limit
    total = sum(s for s, _ in raw_blocks)
    if max_total_chars > 0 and total > max_total_chars:
        kept: list[str] = []
        running = 0
        for size, text in reversed(raw_blocks):
            if kept and running + size > max_total_chars:
                break
            kept.append(text)
            running += size
        raw_blocks_formatted = list(reversed(kept))
    else:
        raw_blocks_formatted = [t for _, t in raw_blocks]

    observation_text = (
        "[历史工具操作记录（仅供参考，不是当前待执行调用）]\n"
        + "\n\n".join(raw_blocks_formatted)
    )
    return SystemMessage(content=observation_text)
