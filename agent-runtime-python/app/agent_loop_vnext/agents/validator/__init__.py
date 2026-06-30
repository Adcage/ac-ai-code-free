"""Validator Agent — 代码校验。"""
from app.agent_loop_vnext.agents import AgentRegistry
from app.agent_loop_vnext.agents.validator.agent import ValidatorAgent

AgentRegistry.register(ValidatorAgent)

__all__ = ["ValidatorAgent"]
