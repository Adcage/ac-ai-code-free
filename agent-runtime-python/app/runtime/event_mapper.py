"""基础事件映射器。

职责：
1. 将引擎无关的 RuntimeEvent 映射为 gRPC CodeGenerationEvent（TEXT_DELTA / DONE / ERROR / STATUS）
2. 将 CLARIFICATION_REQUIRED 折叠为 ask_user TOOL_REQUEST（各引擎共用）
3. 定义 TOOL_CALL / TOOL_RESULT 的映射接口，由各引擎子类实现

各引擎（legacy / vNext）通过继承 ProtoEventMapper 并覆盖 _map_tool_call / _map_tool_result
实现各自特有的工具调用映射和脱敏逻辑。
"""

import json
import logging
import os
import re

from app.grpc import code_generation_pb2
from app.grpc import common_pb2
from app.runtime.events import RuntimeEventType
from app.runtime.event_bus import SequencedRuntimeEvent

logger = logging.getLogger("app.runtime.event_mapper")


# ---------------------------------------------------------------------------
# 通用脱敏工具（各引擎共用）
# ---------------------------------------------------------------------------


def _sanitize_path_in_message(message: str) -> str:
    """替换消息中的文件路径为 [路径已隐藏]。"""
    sanitized = re.sub(r"[A-Za-z]:\\[^\s;,\]]+", "[路径已隐藏]", message)
    sanitized = re.sub(r"/home/[^\s;,\]]+", "[路径已隐藏]", sanitized)
    sanitized = re.sub(r"/var/[^\s;,\]]+", "[路径已隐藏]", sanitized)
    sanitized = re.sub(r"/tmp/[^\s;,\]]+", "[路径已隐藏]", sanitized)
    sanitized = re.sub(r"/opt/[^\s;,\]]+", "[路径已隐藏]", sanitized)
    sanitized = re.sub(r"/usr/[^\s;,\]]+", "[路径已隐藏]", sanitized)
    return sanitized


def _sanitize_path(path: str) -> str:
    """获取路径的 basename，用于脱敏。"""
    return os.path.basename(path) if path else path


# ---------------------------------------------------------------------------
# 通用常量
# ---------------------------------------------------------------------------

_INTERNAL_TYPES = frozenset({
    RuntimeEventType.NODE_STARTED,
    RuntimeEventType.NODE_COMPLETED,
    RuntimeEventType.CAPABILITY_SELECTED,
    RuntimeEventType.MODEL_SELECTED,
    RuntimeEventType.MODE_SWITCHED,
    RuntimeEventType.AGENT_LOOP_ITERATION,
    RuntimeEventType.AGENT_LOOP_COMPLETED,
})

_CODE_GEN_TYPE_MAP = {
    1: common_pb2.SINGLE_FILE,
    2: common_pb2.MULTI_FILE,
    3: common_pb2.VUE_PROJECT,
}

_EVENT_TYPE_MAP: dict[RuntimeEventType, int] = {
    RuntimeEventType.TEXT_DELTA: common_pb2.AI_RESPONSE,
    RuntimeEventType.TOOL_CALL: common_pb2.TOOL_REQUEST,
    RuntimeEventType.TOOL_RESULT: common_pb2.TOOL_EXECUTED,
    RuntimeEventType.RUNTIME_ERROR: common_pb2.ERROR,
    RuntimeEventType.DONE: common_pb2.DONE,
    RuntimeEventType.STATUS: common_pb2.STATUS,
}


# ---------------------------------------------------------------------------
# 基类
# ---------------------------------------------------------------------------


class ProtoEventMapper:
    """事件映射器基类。

    子类必须覆盖 _map_tool_call() 和 _map_tool_result()
    实现引擎特定的工具调用映射和脱敏逻辑。
    """

    def __init__(self) -> None:
        self._emitted_question_set_ids: set[str] = set()

    def reset_question_set_dedupe(self) -> None:
        self._emitted_question_set_ids.clear()

    def _get_agent_name(self, sequenced_event: SequencedRuntimeEvent) -> str:
        """从事件 data 中提取 agent_name。"""
        return sequenced_event.event.data.get("agent_name", "")

    def map_event(
        self, sequenced_event: SequencedRuntimeEvent
    ) -> list[code_generation_pb2.CodeGenerationEvent]:
        """将 RuntimeEvent 映射为 0 到多个 CodeGenerationEvent。"""
        event = sequenced_event.event

        # CLARIFICATION_REQUIRED — 基类统一处理
        if event.event_type == RuntimeEventType.CLARIFICATION_REQUIRED:
            result = self._map_clarification_required(sequenced_event)
            return [result] if result is not None else []

        # 过滤内部事件（所有引擎共用）
        if event.event_type in _INTERNAL_TYPES:
            return []

        # 工具调用 → 引擎子类实现
        if event.event_type == RuntimeEventType.TOOL_CALL:
            return self._map_tool_call(sequenced_event)

        # 工具结果 → 引擎子类实现
        if event.event_type == RuntimeEventType.TOOL_RESULT:
            return self._map_tool_result(sequenced_event)

        # 通用事件映射
        event_type_proto = _EVENT_TYPE_MAP.get(event.event_type)
        if event_type_proto is None:
            logger.warning("unmapped runtime event type: %s", event.event_type)
            return []

        data = event.data
        kwargs: dict = {
            "agent_run_id": str(sequenced_event.agent_run_id),
            "seq": sequenced_event.seq,
            "event_type": event_type_proto,
            "agent_name": self._get_agent_name(sequenced_event),
        }

        if event.event_type == RuntimeEventType.TEXT_DELTA:
            kwargs["ai_response"] = common_pb2.AiResponseData(
                text=data.get("text", ""),
                fallback=data.get("fallback", False),
            )
        elif event.event_type == RuntimeEventType.RUNTIME_ERROR:
            kwargs["error"] = common_pb2.ErrorData(
                message=_sanitize_path_in_message(data.get("message", "")),
                code=data.get("code", 0),
            )
        elif event.event_type == RuntimeEventType.DONE:
            kwargs["done"] = common_pb2.DoneData(
                message=_sanitize_path_in_message(data.get("message", "")),
            )
        elif event.event_type == RuntimeEventType.STATUS:
            kwargs["status"] = common_pb2.StatusData(
                message=data.get("message", ""),
            )

        return [code_generation_pb2.CodeGenerationEvent(**kwargs)]

    # ------------------------------------------------------------------
    # 子类职责
    # ------------------------------------------------------------------

    def _map_tool_call(
        self, sequenced_event: SequencedRuntimeEvent
    ) -> list[code_generation_pb2.CodeGenerationEvent]:
        """子类覆盖：将 TOOL_CALL 映射为 0 到多个 CodeGenerationEvent。"""
        raise NotImplementedError

    def _map_tool_result(
        self, sequenced_event: SequencedRuntimeEvent
    ) -> list[code_generation_pb2.CodeGenerationEvent]:
        """子类覆盖：将 TOOL_RESULT 映射为 0 到多个 CodeGenerationEvent。"""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 共用方法
    # ------------------------------------------------------------------

    def _map_clarification_required(
        self, sequenced_event: SequencedRuntimeEvent
    ) -> code_generation_pb2.CodeGenerationEvent | None:
        """CLARIFICATION_REQUIRED → ask_user TOOL_REQUEST，同一 questionSetId 只下发一次。"""
        data = sequenced_event.event.data or {}
        question_set_id = data.get("questionSetId", "")
        questions = data.get("questions") or []
        if not question_set_id or not questions:
            return None
        if question_set_id in self._emitted_question_set_ids:
            return None
        self._emitted_question_set_ids.add(question_set_id)

        arguments = json.dumps(
            {
                "protocolVersion": data.get("protocolVersion", 1),
                "questionSetId": question_set_id,
                "stage": data.get("stage", ""),
                "questions": questions,
            },
            ensure_ascii=False,
        )
        return code_generation_pb2.CodeGenerationEvent(
            agent_run_id=str(sequenced_event.agent_run_id),
            seq=sequenced_event.seq,
            event_type=common_pb2.TOOL_REQUEST,
            agent_name=self._get_agent_name(sequenced_event),
            tool_request=common_pb2.ToolRequestData(
                id=question_set_id,
                name="ask_user",
                arguments=arguments,
            ),
        )
