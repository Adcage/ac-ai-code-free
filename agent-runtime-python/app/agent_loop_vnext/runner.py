"""vNext Agent 启动器：创建 Agent → 执行 → 返回结果。

Phase 1：直接实例化 ImplementorAgent。
Phase 2：替换为 RouterAgent 决策（从 AgentRegistry 选取）。
Phase 3：支持 Pipeline 多 Agent 串联执行。
"""

import logging

from app.agent_loop_vnext.agents.implementor.agent import ImplementorAgent
from app.agent_loop_vnext.base.agent import Agent
from app.agent_loop_vnext.base.result import AgentResult
from app.runtime.context import ExecutionContext
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.agent_loop_vnext.runner")


async def run_vnext_agent(
    context: ExecutionContext,
    services: RuntimeServices,
) -> AgentResult:
    """vNext Agent 入口——启动 Agent 并执行。

    Phase 1：直接使用 implementor。
    Phase 2：替换为 RouterAgent 决策。
    """
    agent: Agent = ImplementorAgent()
    logger.info(
        "starting vnext agent | agent=%s workspace=%s",
        agent.name, context.workspace_path,
    )
    return await agent.run(context, services)


# ---- 兼容别名 ----
# 保持 `from app.agent_loop_vnext.runner import SingleImplementLoopRunner`
# test_runner.py / test_orchestrator_vnext_routing.py 沿用此导入
class SingleImplementLoopRunner:
    """兼容别名。新代码用 run_vnext_agent() 或直接实例化 Agent。"""

    def __init__(self, context: ExecutionContext, services: RuntimeServices) -> None:
        self._context = context
        self._services = services
        self._agent: Agent | None = None

    @property
    def state(self):
        return self._agent.state if self._agent else None

    async def run(self) -> None:
        self._agent = ImplementorAgent()
        result = await self._agent.run(self._context, self._services)
        _ = result  # 结果通过 state 属性访问
