import pytest

from app.nodes.base import NodeMetadata, RuntimeNode
from app.registries.node_registry import NodeRegistry


class _DummyNode(RuntimeNode):
    def __init__(self, node_id: str, name: str = "dummy"):
        self.metadata = NodeMetadata(id=node_id, name=name)

    async def run(self, context, state, services):
        return state


class TestNodeRegistry:
    def test_register_success(self):
        registry = NodeRegistry()
        node = _DummyNode("test_node")
        registry.register(node)
        assert "test_node" in registry.ids()

    def test_register_duplicate_raises(self):
        registry = NodeRegistry()
        registry.register(_DummyNode("dup"))
        with pytest.raises(ValueError, match="Duplicate"):
            registry.register(_DummyNode("dup"))

    def test_get_success(self):
        registry = NodeRegistry()
        registry.register(_DummyNode("n1"))
        result = registry.get("n1")
        assert result.metadata.id == "n1"

    def test_get_not_found_raises(self):
        registry = NodeRegistry()
        with pytest.raises(KeyError, match="not registered"):
            registry.get("missing")

    def test_ids_returns_all(self):
        registry = NodeRegistry()
        registry.register(_DummyNode("a"))
        registry.register(_DummyNode("b"))
        assert set(registry.ids()) == {"a", "b"}
