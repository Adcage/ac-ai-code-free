"""测试 Runner 集成。"""

import pytest

from app.agent_loop_vnext.runner import SingleImplementLoopRunner
from app.runtime.context import CodeGenType, ExecutionContext, RunMode
from app.runtime.event_bus import EventBus
from app.runtime.events import RuntimeEventType
from app.runtime.services import RuntimeServices


def test_runner_instantiation():
    """Runner 应能正常实例化。"""
    assert hasattr(SingleImplementLoopRunner, "run")


class _FakeReadTool:
    name = "Read"

    async def _arun(self, path: str) -> str:
        return f"read {path}"


@pytest.mark.asyncio
async def test_runner_tool_events_include_implementor_agent_name():
    """当前 vNext 单实现链路发出的工具事件应标记 implementor。"""
    event_bus = EventBus(agent_run_id=1)
    runner = SingleImplementLoopRunner(
        ExecutionContext(
            agent_run_id=1,
            app_id=0,
            session_id=0,
            user_id=0,
            prompt="读取文件",
            code_gen_type=CodeGenType.VUE_PROJECT,
            workspace_path=".",
            run_mode=RunMode.GENERATE,
        ),
        RuntimeServices(event_bus=event_bus),
    )

    messages: list = []
    await runner._execute_tool_calls(
        [{"id": "tool-1", "name": "Read", "args": {"path": "index.html"}}],
        [_FakeReadTool()],
        messages,
    )

    tool_call_event = await event_bus.next_event()
    tool_result_event = await event_bus.next_event()

    assert tool_call_event.event.event_type == RuntimeEventType.TOOL_CALL
    assert tool_call_event.event.data["agent_name"] == "implementor"
    assert tool_result_event.event.event_type == RuntimeEventType.TOOL_RESULT
    assert tool_result_event.event.data["agent_name"] == "implementor"
