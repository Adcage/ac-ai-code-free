"""Planner Agent — 技术规划师。"""

import logging
from typing import Any

from app.agent_loop_vnext.agents.planner.prompt import PLANNER_SYSTEM_PROMPT
from app.agent_loop_vnext.base.agent import Agent
from app.agent_loop_vnext.base.result import AgentResult
from app.agent_loop_vnext.shared.tools.file_tools import (
    GlobTool,
    GrepTool,
    ReadTool,
    WriteTool,
)
from app.tools.file_tools import FileTools

logger = logging.getLogger("app.agent_loop_vnext.agents.planner.agent")


class PlannerAgent(Agent):
    """技术规划师：理解需求，输出 .agent/spec.md。"""

    name = "planner"
    description = "技术规划，输出详细的设计文档"

    def __init__(self) -> None:
        super().__init__()

    def create_tools(
        self,
        file_tools: FileTools,
        services: Any,
    ) -> list[Any]:
        return [
            ReadTool(file_tools=file_tools),
            WriteTool(file_tools=file_tools),
            GlobTool(file_tools=file_tools),
            GrepTool(file_tools=file_tools),
        ]

    def build_system_prompt(
        self,
        context: Any,
        services: Any,
    ) -> str:
        return PLANNER_SYSTEM_PROMPT

    async def run(
        self,
        context: Any,
        services: Any,
    ) -> AgentResult:
        result = await super().run(context, services)

        # 检查模型是否输出了 needs_clarification 请求
        if result.message and result.message.strip().upper().startswith("NEEDS_CLARIFICATION:"):
            result.status = "needs_clarification"
            result.message = result.message[len("NEEDS_CLARIFICATION:"):].strip()

        return result
