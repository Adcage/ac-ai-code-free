"""代码实现 Agent — ImplementorAgent。"""
from app.agent_loop_vnext.agents import AgentRegistry
from app.agent_loop_vnext.agents.implementor.agent import ImplementorAgent

AgentRegistry.register(ImplementorAgent)

__all__ = ["ImplementorAgent"]
