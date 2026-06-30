from app.agent_loop_vnext.agents.implementor.tools import create_implementor_tools
from app.agent_loop_vnext.base.state import AgentRunState
from app.tools.file_tools import FileTools


def test_create_implementor_tools_accepts_agent_run_state_for_conductor():
    """Conductor 派遣 implementor 时，应允许传入通用 AgentRunState。"""
    file_tools = FileTools("/tmp/test-workspace")
    tools = create_implementor_tools(file_tools=file_tools, state=AgentRunState())

    tool_names = {tool.name for tool in tools}
    assert "Read" in tool_names
    assert "LoadSkill" in tool_names
    assert "AskUser" in tool_names
