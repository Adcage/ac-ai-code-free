"""Legacy Agent Loop 事件映射器。

存量的旧链路工具调用映射逻辑。后续遗弃 legacy 引擎时，删除此文件即可。
"""

import json
import logging
import os
import re

from app.grpc import code_generation_pb2
from app.grpc import common_pb2
from app.runtime.event_mapper import (
    ProtoEventMapper,
    _sanitize_path,
    _sanitize_path_in_message,
)
from app.runtime.event_bus import SequencedRuntimeEvent

logger = logging.getLogger("app.agent_loop.event_mapper")


# ---------------------------------------------------------------------------
# Legacy 工具常量
# ---------------------------------------------------------------------------

_VISIBLE_TOOLS = frozenset({
    # legacy agent_loop 工具名
    "write_file",
    "read_file",
    "read_dir",
    "run_checks",
    "view",
    "create",
    "str_replace",
    "insert",
    # vNext 工具名（存量映射保留，实际 vNext 链路不走这里）
    "Read",
    "Write",
    "Edit",
    "Insert",
    "Glob",
    "Grep",
    "load_skill",
    "Bash",
})

_STATUS_TOOLS: dict[str, str] = {
    "select_skill": "正在选择设计方案...",
    "write_plan": "正在制定实现计划...",
    "read_asset": "正在查询设计资源...",
    "run_command": "正在执行命令...",
    "decide_route": "正在路由决策...",
    "decide_validation": "正在输出校验结论...",
    "request_replan": "正在请求重新规划...",
    "submit_requirement_brief": "正在提交需求摘要...",
    "record_project_inspection": "正在记录项目检查...",
    "choose_skill": "正在选择设计方案...",
    "propose_design": "正在提出设计建议...",
    "confirm_design": "正在确认设计方案...",
    "write_implementation_plan": "正在编写实施计划...",
    "plan_stage_guard": "正在处理阶段状态...",
    "confirm_generation_mode": "正在确认生成模式...",
    "complete_implementation": "正在提交实现完成...",
    "submit_validation_report": "正在提交校验报告...",
}

_HIDDEN_TOOLS = frozenset({"finish", "ask_user"})


# ---------------------------------------------------------------------------
# Legacy 脱敏逻辑
# ---------------------------------------------------------------------------


def _sanitize_tool_arguments(tool_name: str, arguments_str: str) -> str:
    """Legacy 工具参数脱敏。"""
    if not arguments_str:
        return arguments_str
    try:
        args = json.loads(arguments_str) if isinstance(arguments_str, str) else dict(arguments_str)
    except (json.JSONDecodeError, TypeError, ValueError):
        return _sanitize_path_in_message(str(arguments_str))

    if tool_name == "write_file":
        args.pop("content", None)
        if "relative_path" in args:
            args["relativeFilePath"] = _sanitize_path(args.pop("relative_path"))
        if "contentLength" not in args:
            pass
    elif tool_name == "read_file":
        if "relative_path" in args:
            args["relativeFilePath"] = _sanitize_path(args.pop("relative_path"))
        args.pop("scope", None)
    elif tool_name == "read_dir":
        if "relative_path" in args:
            args["relativeDirPath"] = _sanitize_path(args.pop("relative_path"))
    elif tool_name == "ask_user":
        pass
    elif tool_name == "view":
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
        args.pop("view_range", None)
    elif tool_name == "create":
        args.pop("content", None)
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
    elif tool_name == "str_replace":
        args.pop("new_str", None)
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
        args["oldStrLength"] = len(args.get("old_str", ""))
        args.pop("old_str", None)
    elif tool_name == "insert":
        args.pop("insert_text", None)
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
    elif tool_name == "Read":
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
        args.pop("view_range", None)
    elif tool_name == "Write":
        args.pop("content", None)
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
    elif tool_name == "Edit":
        args.pop("old_str", None)
        args.pop("new_str", None)
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
    elif tool_name == "Insert":
        args.pop("insert_text", None)
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
    elif tool_name in ("Glob", "Grep"):
        if "path" in args:
            args["path"] = _sanitize_path(args["path"])
    elif tool_name == "load_skill":
        pass
    elif tool_name == "Bash":
        if "command" in args:
            cmd = args["command"]
            args["command"] = (cmd[:200] + "...") if len(cmd) > 200 else cmd
    else:
        for key in list(args.keys()):
            val = str(args[key])
            args[key] = _sanitize_path_in_message(val)

    return json.dumps(args, ensure_ascii=False)


def _sanitize_tool_result(tool_name: str, result_str: str) -> str:
    """Legacy 工具结果脱敏。"""
    if not result_str:
        return result_str
    if tool_name in ("write_file", "read_dir", "create", "str_replace", "insert", "view"):
        return _sanitize_path_in_message(result_str)
    if tool_name == "read_file":
        return _sanitize_path_in_message(result_str)
    if tool_name in ("Read", "Write", "Edit", "Insert", "Glob", "Grep", "load_skill", "Bash"):
        return _sanitize_path_in_message(result_str)
    if tool_name == "ask_user":
        return _sanitize_path_in_message(result_str)
    return _sanitize_path_in_message(result_str)


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class LegacyEventMapper(ProtoEventMapper):
    """Legacy Agent Loop 事件映射器。"""

    def _map_tool_call(
        self, sequenced_event: SequencedRuntimeEvent
    ) -> list[code_generation_pb2.CodeGenerationEvent]:
        data = sequenced_event.event.data
        tool_name = data.get("name", "")

        if tool_name in _HIDDEN_TOOLS:
            return []

        if tool_name in _STATUS_TOOLS:
            return [code_generation_pb2.CodeGenerationEvent(
                agent_run_id=str(sequenced_event.agent_run_id),
                seq=sequenced_event.seq,
                event_type=common_pb2.STATUS,
                status=common_pb2.StatusData(
                    message=_STATUS_TOOLS[tool_name],
                ),
            )]

        if tool_name in _VISIBLE_TOOLS:
            sanitized_args = _sanitize_tool_arguments(tool_name, data.get("arguments", ""))
            return [code_generation_pb2.CodeGenerationEvent(
                agent_run_id=str(sequenced_event.agent_run_id),
                seq=sequenced_event.seq,
                event_type=common_pb2.TOOL_REQUEST,
                tool_request=common_pb2.ToolRequestData(
                    id=data.get("id", ""),
                    name=tool_name,
                    arguments=sanitized_args,
                ),
            )]

        status_msg = _STATUS_TOOLS.get(tool_name)
        if status_msg:
            return [code_generation_pb2.CodeGenerationEvent(
                agent_run_id=str(sequenced_event.agent_run_id),
                seq=sequenced_event.seq,
                event_type=common_pb2.STATUS,
                status=common_pb2.StatusData(message=status_msg),
            )]

        logger.warning("unclassified tool in TOOL_CALL: %s", tool_name)
        return []

    def _map_tool_result(
        self, sequenced_event: SequencedRuntimeEvent
    ) -> list[code_generation_pb2.CodeGenerationEvent]:
        data = sequenced_event.event.data
        tool_name = data.get("name", "")

        if tool_name in _HIDDEN_TOOLS:
            return []

        if tool_name == "ask_user":
            return []

        if tool_name == "complete_implementation":
            result = _sanitize_tool_result(tool_name, data.get("result", ""))
            events: list[code_generation_pb2.CodeGenerationEvent] = []
            events.append(code_generation_pb2.CodeGenerationEvent(
                agent_run_id=str(sequenced_event.agent_run_id),
                seq=sequenced_event.seq,
                event_type=common_pb2.STATUS,
                status=common_pb2.StatusData(
                    message="正在提交实现完成完成",
                ),
            ))
            events.append(code_generation_pb2.CodeGenerationEvent(
                agent_run_id=str(sequenced_event.agent_run_id),
                seq=sequenced_event.seq,
                event_type=common_pb2.TOOL_EXECUTED,
                tool_executed=common_pb2.ToolExecutedData(
                    id=data.get("id", ""),
                    name=tool_name,
                    arguments=_sanitize_tool_arguments(tool_name, data.get("arguments", "")),
                    result=result,
                ),
            ))
            return events

        if tool_name in _STATUS_TOOLS:
            return [code_generation_pb2.CodeGenerationEvent(
                agent_run_id=str(sequenced_event.agent_run_id),
                seq=sequenced_event.seq,
                event_type=common_pb2.STATUS,
                status=common_pb2.StatusData(
                    message=f"{_STATUS_TOOLS[tool_name].rstrip('.')}完成",
                ),
            )]

        if tool_name in _VISIBLE_TOOLS:
            sanitized_args = _sanitize_tool_arguments(tool_name, data.get("arguments", ""))
            sanitized_result = _sanitize_tool_result(tool_name, data.get("result", ""))
            return [code_generation_pb2.CodeGenerationEvent(
                agent_run_id=str(sequenced_event.agent_run_id),
                seq=sequenced_event.seq,
                event_type=common_pb2.TOOL_EXECUTED,
                tool_executed=common_pb2.ToolExecutedData(
                    id=data.get("id", ""),
                    name=tool_name,
                    arguments=sanitized_args,
                    result=sanitized_result,
                ),
            )]

        status_msg = _STATUS_TOOLS.get(tool_name)
        if status_msg:
            return [code_generation_pb2.CodeGenerationEvent(
                agent_run_id=str(sequenced_event.agent_run_id),
                seq=sequenced_event.seq,
                event_type=common_pb2.STATUS,
                status=common_pb2.StatusData(
                    message=f"{status_msg.rstrip('.')}完成",
                ),
            )]

        logger.warning("unclassified tool in TOOL_RESULT: %s", tool_name)
        return []
