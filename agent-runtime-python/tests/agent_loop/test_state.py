import pytest

from app.agent_loop.state import AgentLoopState
from app.runtime.state import ToolCallRecord


class TestAgentLoopState:
    def test_default_state(self):
        state = AgentLoopState()
        assert state.mode == "plan"
        assert state.status == "running"
        assert state.iteration == 0
        assert state.max_iterations == 50
        assert state.mode_switches == 0
        assert state.max_mode_switches == 6
        assert state.selected_capabilities is None
        assert state.implementation_outline is None
        assert state.clarification_questions == []

    def test_mode_transition(self):
        state = AgentLoopState()
        state.mode = "implement"
        state.mode_switches += 1
        assert state.mode == "implement"
        assert state.mode_switches == 1

    def test_completed_status(self):
        state = AgentLoopState(status="completed")
        assert state.status == "completed"

    def test_max_iterations_exceeded(self):
        state = AgentLoopState(iteration=51, max_iterations=50)
        assert state.iteration >= state.max_iterations

    def test_waiting_for_user_status(self):
        state = AgentLoopState(status="waiting_for_user")
        assert state.status == "waiting_for_user"


class TestAgentLoopStateSerialization:
    def test_serialize_deserialize_roundtrip(self):
        state = AgentLoopState()
        state.mode = "implement"
        state.iteration = 5
        state.mode_switches = 2
        state.selected_skill_id = "ui-ux-pro-max"
        state.implementation_outline = {"text": "test plan"}
        state.clarification_questions = [{"id": "q1", "question": "颜色？"}]
        state.files_touched = ["src/App.vue", "src/main.ts"]
        state.executed_tool_calls = [
            ToolCallRecord(id="t1", name="read_file", arguments={"relative_path": "src/App.vue"}, result="file content"),
            ToolCallRecord(id="t2", name="ask_user", arguments={"question": "颜色？"}, result="已向用户提问"),
        ]
        state.conversation_messages = [{"role": "user", "content": "做一个仪表盘"}]
        state.resolved_model = {"provider": "openai", "modelName": "gpt-4", "apiKey": "sk-secret"}
        state.plan_iterations = 3

        json_str = state.serialize()
        restored = AgentLoopState.deserialize(json_str)

        assert restored.mode == "implement"
        assert restored.iteration == 5
        assert restored.mode_switches == 2
        assert restored.selected_skill_id == "ui-ux-pro-max"
        assert restored.implementation_outline == {"text": "test plan"}
        assert len(restored.clarification_questions) == 1
        assert restored.files_touched == ["src/App.vue", "src/main.ts"]
        assert len(restored.executed_tool_calls) == 2
        assert restored.executed_tool_calls[0].name == "read_file"
        assert restored.executed_tool_calls[1].name == "ask_user"
        assert len(restored.conversation_messages) == 1
        assert restored.resolved_model["provider"] == "openai"
        assert "apiKey" not in restored.resolved_model
        assert restored.plan_iterations == 3

    def test_serialize_waiting_for_user(self):
        state = AgentLoopState()
        state.status = "waiting_for_user"
        json_str = state.serialize()
        restored = AgentLoopState.deserialize(json_str)
        assert restored.status == "waiting_for_user"

    def test_deserialize_empty_fields(self):
        state = AgentLoopState()
        json_str = state.serialize()
        restored = AgentLoopState.deserialize(json_str)
        assert restored.mode == "plan"
        assert restored.iteration == 0
        assert restored.files_touched == []
        assert restored.executed_tool_calls == []

    def test_serialize_strips_api_key(self):
        state = AgentLoopState()
        state.resolved_model = {"provider": "openai", "modelName": "gpt-4", "apiKey": "sk-super-secret"}
        json_str = state.serialize()
        import json
        data = json.loads(json_str)
        assert "apiKey" not in data["resolved_model"]
