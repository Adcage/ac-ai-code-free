"""Conductor Agent — 调度与编排。"""
from app.agent_loop_vnext.agents import AgentRegistry
from app.agent_loop_vnext.agents.conductor.agent import ConductorAgent

AgentRegistry.register(ConductorAgent)

__all__ = ["ConductorAgent"]
