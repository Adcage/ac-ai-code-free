"""Conductor Agent — 产品经理/指挥家。

负责需求分析、调度子 Agent、审查结果。
"""

import logging
from typing import Any

from app.agent_loop_vnext.agents import AgentRegistry
from app.agent_loop_vnext.agents.conductor.prompt import ConductorPromptBuilder
from app.agent_loop_vnext.agents.conductor.tools import create_conductor_tools
from app.agent_loop_vnext.base.agent import Agent
from app.agent_loop_vnext.base.result import AgentResult
from app.agent_loop_vnext.base.state import ConductorState
from app.runtime.context import ExecutionContext
from app.runtime.services import RuntimeServices
from app.tools.file_tools import FileTools

logger = logging.getLogger("app.agent_loop_vnext.agents.conductor.agent")


class ConductorAgent(Agent):
    """产品经理/指挥家：了解需求 → 调度子 Agent → 汇总结果。"""

    name = "conductor"
    description = "了解用户需求，调度子 Agent 完成任务"

    def __init__(self) -> None:
        super().__init__()
        self._state_mgr = ConductorState()
        self._user_prompt: str = ""
        self._context: ExecutionContext | None = None

    async def run(
        self,
        context: ExecutionContext,
        services: RuntimeServices,
    ) -> AgentResult:
        """在执行前保存 context，供 create_tools/build_system_prompt 使用。"""
        self._context = context
        self._user_prompt = context.prompt or ""
        return await super().run(context, services)

    def create_tools(
        self,
        file_tools: FileTools,
        services: Any,
    ) -> list[Any]:
        return create_conductor_tools(
            file_tools=file_tools,
            state=self._state,
            services=services,
            context=self._context,
            user_prompt=self._user_prompt,
            conductor_state=self._state_mgr,
        )

    def build_system_prompt(
        self,
        context: ExecutionContext,
        services: RuntimeServices,
    ) -> str:
        agents = AgentRegistry.list_agents()
        return ConductorPromptBuilder(
            agent_list=agents,
            state=self._state_mgr,
        ).build()
