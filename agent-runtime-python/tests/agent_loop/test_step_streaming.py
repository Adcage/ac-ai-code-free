from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessageChunk

from app.agent_loop.nodes.step_base import _execute_single_step, _stream_invoke
from app.agent_loop.state import AgentLoopState
from app.runtime.context import CodeGenType, ExecutionContext, RunMode
from app.runtime.events import RuntimeEventType


class StreamingModel:
    def bind_tools(self, _tools):
        return self

    async def astream(self, _messages):
        yield AIMessageChunk(content="你")
        yield AIMessageChunk(content="好")


def make_event_bus():
    event_bus = MagicMock()
    event_bus.emit = AsyncMock()
    return event_bus


def emitted_texts(event_bus) -> list[str]:
    return [
        call.args[0].data["text"]
        for call in event_bus.emit.await_args_list
        if call.args[0].event_type == RuntimeEventType.TEXT_DELTA
    ]


@pytest.mark.asyncio
async def test_stream_invoke_emits_each_delta_once():
    event_bus = make_event_bus()

    text, tool_calls, _ = await _stream_invoke(StreamingModel(), [], event_bus)

    assert text == "你好"
    assert tool_calls == []
    assert emitted_texts(event_bus) == ["你", "好"]


@pytest.mark.asyncio
async def test_execute_single_step_does_not_reemit_aggregate_text():
    event_bus = make_event_bus()
    factory = MagicMock()
    factory.create.return_value = StreamingModel()
    services = SimpleNamespace(chat_model_factory=factory, event_bus=event_bus)
    state = AgentLoopState(
        resolved_model={"provider": "test", "modelName": "streaming-test"},
    )
    context = ExecutionContext(
        agent_run_id=1,
        app_id=1,
        session_id=1,
        user_id=1,
        prompt="创建登录页",
        code_gen_type=CodeGenType.VUE_PROJECT,
        workspace_path="C:/tmp/workspace",
        run_mode=RunMode.GENERATE,
    )

    result = await _execute_single_step(
        state,
        context,
        services,
        "系统规则",
        [],
        {},
        MagicMock(),
    )

    assert emitted_texts(event_bus) == ["你", "好"]
    assert result.model_response_text == "你好"
