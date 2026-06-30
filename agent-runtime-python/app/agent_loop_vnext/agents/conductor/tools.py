"""Conductor Agent 的工具集绑定。

每个 Agent 的 tools.py 从 shared/tools/ 中挑选工具并注入依赖。
"""

from app.agent_loop_vnext.shared.tools.ask_user_tool import AskUserTool
from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.agent_loop_vnext.shared.tools.delegate_tool import DelegateToAgentTool
from app.agent_loop_vnext.shared.tools.file_tools import (
    GlobTool,
    GrepTool,
    ReadTool,
    WriteTool,
)
from app.tools.file_tools import FileTools


def create_conductor_tools(
    file_tools: FileTools,
    state=None,
    services=None,
    context=None,
    user_prompt: str = "",
    conductor_state=None,
) -> list[AgentTool]:
    """创建 Conductor Agent 的工具集。"""
    from app.agent_loop_vnext.agents import AgentRegistry

    return [
        ReadTool(file_tools=file_tools),
        WriteTool(file_tools=file_tools, allowed_prefix=".agent/"),
        GlobTool(file_tools=file_tools),
        GrepTool(file_tools=file_tools),
        AskUserTool(state=state),
        DelegateToAgentTool(
            agent_registry=AgentRegistry,
            services=services,
            parent_context=context,
            user_prompt=user_prompt,
            conductor_state=conductor_state,
        ),
    ]
