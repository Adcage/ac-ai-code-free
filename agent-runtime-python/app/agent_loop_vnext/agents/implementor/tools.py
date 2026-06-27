"""Implementor Agent 的工具集绑定。

每个 Agent 的 tools.py 从 shared/tools/ 中挑选工具并注入 FileTools 依赖。
"""

from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.agent_loop_vnext.shared.tools.file_tools import (
    EditTool,
    GlobTool,
    GrepTool,
    InsertTool,
    ReadTool,
    WriteTool,
)
from app.tools.file_tools import FileTools


def create_implementor_tools(file_tools: FileTools) -> list[AgentTool]:
    """创建 implementor Agent 的工具集。"""
    return [
        ReadTool(file_tools=file_tools),
        WriteTool(file_tools=file_tools),
        EditTool(file_tools=file_tools),
        InsertTool(file_tools=file_tools),
        GlobTool(file_tools=file_tools),
        GrepTool(file_tools=file_tools),
    ]
