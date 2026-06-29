"""vNext AskUserTool 单元测试。"""

import pytest

from app.agent_loop_vnext.shared.tools.ask_user_tool import AskUserTool, AskUserInput
from app.agent_loop_vnext.state import SingleImplementState
from app.runtime.events import RuntimeEvent, RuntimeEventType


class _StubEventBus:
    """记录发射的事件，用于断言。"""

    def __init__(self):
        self.events: list[RuntimeEvent] = []

    async def emit(self, event: RuntimeEvent):
        self.events.append(event)


class TestAskUserInputTypeNormalization:
    """inputType 归一化测试。"""

    @pytest.mark.asyncio
    async def test_single_choice_normalized_to_single_select(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_choice",
             "options": [{"id": "dark", "label": "深色"}, {"id": "light", "label": "浅色"}]}
        ])
        assert "已向用户提问" in result
        assert state.status == "waiting_for_user"

    @pytest.mark.asyncio
    async def test_multi_normalized_to_multi_select(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "功能？", "inputType": "multi",
             "options": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}]}
        ])
        assert state.status == "waiting_for_user"

    @pytest.mark.asyncio
    async def test_text_type_rejected(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "描述", "inputType": "text", "options": []}
        ])
        assert "错误" in result
        assert "不被支持" in result
        assert state.status == "running"


class TestAskUserValidation:
    """参数校验测试。"""

    @pytest.mark.asyncio
    async def test_empty_questions_rejected(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[])
        assert "错误" in result
        assert state.status == "running"

    @pytest.mark.asyncio
    async def test_no_options_rejected(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "选一个", "inputType": "single_select", "options": []}
        ])
        assert "错误" in result
        assert "options" in result

    @pytest.mark.asyncio
    async def test_no_state_returns_error(self):
        tool = AskUserTool(state=None, event_bus=_StubEventBus())
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_select",
             "options": [{"id": "dark", "label": "深色"}]}
        ])
        assert "错误" in result


class TestAskUserEventEmission:
    """事件发射和状态设置测试。"""

    @pytest.mark.asyncio
    async def test_emits_clarification_required(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_select",
             "options": [{"id": "dark", "label": "深色"}, {"id": "light", "label": "浅色"}]}
        ])
        assert any(e.event_type == RuntimeEventType.CLARIFICATION_REQUIRED for e in bus.events)
        clarification = next(e for e in bus.events if e.event_type == RuntimeEventType.CLARIFICATION_REQUIRED)
        assert "questionSetId" in clarification.data
        assert len(clarification.data["questions"]) == 1

    @pytest.mark.asyncio
    async def test_sets_waiting_for_user_status(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_select",
             "options": [{"id": "dark", "label": "深色"}]}
        ])
        assert state.status == "waiting_for_user"
        assert state.pending_question is not None
        assert "questionSetId" in state.pending_question

    @pytest.mark.asyncio
    async def test_pending_question_stores_normalized_data(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_choice",
             "options": [{"id": "dark", "label": "深色"}, {"id": "light", "label": "浅色"}]}
        ])
        assert state.pending_question["questions"][0]["inputType"] == "single_select"


class TestAskUserOptionNormalization:
    """选项归一化测试。"""

    @pytest.mark.asyncio
    async def test_string_option_normalized_to_dict(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        await tool._arun(questions=[
            {"id": "q1", "prompt": "选一个", "inputType": "single_select",
             "options": ["dark", "light"]}
        ])
        q = state.pending_question["questions"][0]
        assert q["options"][0] == {"id": "dark", "label": "dark", "description": "", "recommended": False}
        assert q["options"][1] == {"id": "light", "label": "light", "description": "", "recommended": False}
