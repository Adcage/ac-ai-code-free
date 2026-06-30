"""Planner Agent — 技术规划。"""
from app.agent_loop_vnext.agents import AgentRegistry
from app.agent_loop_vnext.agents.planner.agent import PlannerAgent

AgentRegistry.register(PlannerAgent)

__all__ = ["PlannerAgent"]
