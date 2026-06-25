"""测试 AgentTool 基类"""

from app.agent_loop_vnext.shared.tools.base import AgentTool


def test_agent_tool_inherits_from_base_tool():
    """AgentTool 必须是 BaseTool 的子类。"""
    from langchain_core.tools import BaseTool
    assert issubclass(AgentTool, BaseTool)


def test_agent_tool_default_tool_id():
    """tool_id 默认为空字符串。"""
    assert AgentTool.model_fields["tool_id"].default == ""


def test_agent_tool_rebuild_history_context_default():
    """rebuild_history_context 默认实现返回 result 或空字符串。"""

    class FakeRecord:
        result = "some result"

    class TestTool(AgentTool):
        name: str = "test_tool"
        description: str = "test tool for unit testing"
        async def _arun(self) -> str:
            return "done"

    tool = TestTool()
    result = tool.rebuild_history_context(FakeRecord())
    assert result == "some result"

    # 没有 result 时返回空字符串
    class FakeRecordEmpty:
        pass

    result_empty = tool.rebuild_history_context(FakeRecordEmpty())
    assert result_empty == ""
