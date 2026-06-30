"""agent_name 在事件链路中正确传递的单元测试。"""

import pytest

from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.event_bus import EventBus, SequencedRuntimeEvent
from app.agent_loop_vnext.event_mapper import VNextEventMapper
from app.grpc import common_pb2, code_generation_pb2
from app.runtime.event_mapper import ProtoEventMapper


# ---------------------------------------------------------------------------
# VNextEventMapper 传递 agent_name 到 gRPC proto
# ---------------------------------------------------------------------------


def _make_seq_event(event_type: RuntimeEventType, data: dict, agent_run_id: int = 1, seq: int = 1) -> SequencedRuntimeEvent:
    """构造带 agent_name 的 SequencedRuntimeEvent。"""
    return SequencedRuntimeEvent(
        agent_run_id=agent_run_id,
        seq=seq,
        event=RuntimeEvent(event_type, data),
    )


def test_tool_call_event_mapper_passes_agent_name():
    """TOOL_CALL 事件映射后 CodeGenerationEvent.agent_name 应正确传递。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.TOOL_CALL,
        {"id": "tc-1", "name": "Read", "arguments": {"path": "App.vue"}, "agent_name": "implementor"},
    )
    events = mapper.map_event(seq_event)
    # TOOL_CALL → TOOL_REQUEST + STATUS（两个事件）
    assert len(events) == 2
    # 两个事件都应该有 agent_name
    for ev in events:
        assert ev.agent_name == "implementor"


def test_tool_result_event_mapper_passes_agent_name():
    """TOOL_RESULT 事件映射后 CodeGenerationEvent.agent_name 应正确传递。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.TOOL_RESULT,
        {"id": "tc-1", "name": "Read", "result": "file content", "agent_name": "implementor"},
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].agent_name == "implementor"
    assert events[0].event_type == common_pb2.TOOL_EXECUTED


def test_text_delta_event_mapper_passes_agent_name():
    """TEXT_DELTA 事件映射后 CodeGenerationEvent.agent_name 应正确传递。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.TEXT_DELTA,
        {"text": "hello", "agent_name": "implementor"},
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].agent_name == "implementor"
    assert events[0].event_type == common_pb2.AI_RESPONSE


def test_done_event_mapper_passes_agent_name():
    """DONE 事件映射后 CodeGenerationEvent.agent_name 应正确传递。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.DONE,
        {"message": "对话完成", "agent_name": "implementor"},
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].agent_name == "implementor"
    assert events[0].event_type == common_pb2.DONE


def test_error_event_mapper_passes_agent_name():
    """RUNTIME_ERROR 事件映射后 CodeGenerationEvent.agent_name 应正确传递。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.RUNTIME_ERROR,
        {"message": "模型超时", "code": 60001, "agent_name": "implementor"},
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].agent_name == "implementor"
    assert events[0].event_type == common_pb2.ERROR


def test_status_event_mapper_passes_agent_name():
    """STATUS 事件映射后 CodeGenerationEvent.agent_name 应正确传递。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.STATUS,
        {"message": "正在查看 App.vue", "agent_name": "planner"},
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].agent_name == "planner"


def test_agent_name_empty_when_missing():
    """事件 data 中无 agent_name 时，proto 事件 agent_name 应为空串。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.TEXT_DELTA,
        {"text": "hello"},  # 无 agent_name
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].agent_name == ""


def test_clarification_required_passes_agent_name():
    """CLARIFICATION_REQUIRED 映射后 CodeGenerationEvent.agent_name 应正确传递。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.CLARIFICATION_REQUIRED,
        {
            "questionSetId": "qs_abc123",
            "protocolVersion": 1,
            "questions": [{"id": "q1", "prompt": "选择框架", "inputType": "single_select", "required": True, "options": [{"id": "vue", "label": "Vue"}]}],
            "agent_name": "implementor",
        },
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].agent_name == "implementor"
    assert events[0].event_type == common_pb2.TOOL_REQUEST


# ---------------------------------------------------------------------------
# AGENT_START 事件测试
# ---------------------------------------------------------------------------


def test_agent_start_maps_to_correct_proto_type():
    """AGENT_START RuntimeEvent 映射为 gRPC AGENT_START 事件。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.AGENT_START,
        {"agent_name": "planner"},
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].event_type == common_pb2.AGENT_START


def test_agent_start_passes_agent_name():
    """AGENT_START 事件的 agent_name 正确传递。"""
    mapper = VNextEventMapper(is_test=True)
    seq_event = _make_seq_event(
        RuntimeEventType.AGENT_START,
        {"agent_name": "implementor"},
    )
    events = mapper.map_event(seq_event)
    assert len(events) == 1
    assert events[0].agent_name == "implementor"


# ---------------------------------------------------------------------------
# AgentTool.agent_name 属性测试
# ---------------------------------------------------------------------------


def test_agent_tool_has_agent_name_attribute():
    """AgentTool 基类应有 agent_name 属性，默认空串。"""
    from app.agent_loop_vnext.shared.tools.base import AgentTool

    class _DummyTool(AgentTool):
        name: str = "dummy"
        description: str = "dummy"

        def _run(self, *args, **kwargs) -> str:
            return "ok"

    tool = _DummyTool()
    assert tool.agent_name == ""


def test_agent_tool_agent_name_can_be_set():
    """AgentTool.agent_name 可以被注入。"""
    from app.agent_loop_vnext.shared.tools.base import AgentTool

    class _DummyTool(AgentTool):
        name: str = "dummy"
        description: str = "dummy"

        def _run(self, *args, **kwargs) -> str:
            return "ok"

    tool = _DummyTool()
    tool.agent_name = "implementor"
    assert tool.agent_name == "implementor"
