"""测试 Implementor 工具绑定。"""

from app.agent_loop_vnext.agents.implementor.tools import create_implementor_tools
from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.tools.file_tools import FileTools, Workspace


def test_create_implementor_tools_returns_6_tools():
    """implementor 应绑定 6 个工具。"""
    ws = Workspace("/tmp/test")
    ft = FileTools(ws)
    tools = create_implementor_tools(ft)
    assert len(tools) == 6


def test_create_implementor_tools_all_are_agent_tools():
    """所有工具都应是 AgentTool 子类。"""
    ws = Workspace("/tmp/test")
    ft = FileTools(ws)
    tools = create_implementor_tools(ft)
    for t in tools:
        assert isinstance(t, AgentTool)


def test_create_implementor_tools_has_correct_names():
    """工具名应为 Read, Write, Edit, Insert, Glob, Grep。"""
    ws = Workspace("/tmp/test")
    ft = FileTools(ws)
    tools = create_implementor_tools(ft)
    names = {t.name for t in tools}
    assert names == {"Read", "Write", "Edit", "Insert", "Glob", "Grep"}
