"""AgentRegistry 单元测试。"""

import pytest

from app.agent_loop_vnext.agents import AgentRegistry
from app.agent_loop_vnext.base.agent import Agent


class _DummyAgent(Agent):
    """测试用 Agent。"""
    name = "dummy"
    description = "dummy agent for testing"

    def create_tools(self, file_tools, services):
        return []

    def build_system_prompt(self, context, services):
        return "dummy"


def test_agent_registry_register_and_get():
    """注册 Agent 后可通过 get 获取实例。"""
    AgentRegistry.register(_DummyAgent)
    agent = AgentRegistry.get("dummy")
    assert isinstance(agent, _DummyAgent)
    assert agent.name == "dummy"


def test_agent_registry_get_unregistered_raises():
    """获取未注册的 Agent 抛出 KeyError。"""
    with pytest.raises(KeyError):
        AgentRegistry.get("nonexistent")


def test_agent_registry_list_agents():
    """list_agents 返回所有注册信息。"""
    agents = AgentRegistry.list_agents()
    names = {a["name"] for a in agents}
    assert "dummy" in names
    # implementor 也应被注册
    assert "implementor" in names


def test_agent_registry_has():
    """has 方法返回正确状态。"""
    assert AgentRegistry.has("dummy")
    assert not AgentRegistry.has("ghost")


def test_agent_registry_get_returns_new_instance():
    """每次 get 返回新的 Agent 实例。"""
    a1 = AgentRegistry.get("dummy")
    a2 = AgentRegistry.get("dummy")
    assert a1 is not a2
