"""Agent 注册中心。

提供 agents 的注册、发现和实例化。
Phase 1：手动注册已有 Agent。
Phase 2：Router Agent 通过 list_agents() 了解可选 Agent。
"""

from typing import Type

from app.agent_loop_vnext.base.agent import Agent


class AgentRegistry:
    """Agent 注册与发现。"""

    _agents: dict[str, Type[Agent]] = {}

    @classmethod
    def register(cls, agent_cls: Type[Agent]) -> Type[Agent]:
        """注册 Agent 类。返回原类（可作装饰器）。"""
        name = agent_cls.name
        cls._agents[name] = agent_cls
        return agent_cls

    @classmethod
    def get(cls, name: str) -> Agent:
        """获取 Agent 实例。"""
        agent_cls = cls._agents.get(name)
        if agent_cls is None:
            raise KeyError(
                f"未注册的 Agent: {name}。"
                f" 已注册: {list(cls._agents.keys())}"
            )
        return agent_cls()

    @classmethod
    def list_agents(cls) -> list[dict]:
        """列出所有已注册的 Agent 元信息。"""
        return [
            {"name": n, "description": c.description}
            for n, c in cls._agents.items()
        ]

    @classmethod
    def has(cls, name: str) -> bool:
        """检查 Agent 是否已注册。"""
        return name in cls._agents
