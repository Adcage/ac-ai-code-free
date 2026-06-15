import pytest

from app.prompts.modules import PromptModule
from app.prompts.composer import PromptComposer
from app.registries.prompt_module_registry import PromptModuleRegistry


class _HelloModule(PromptModule):
    id = "hello"

    def render(self, context, state):
        return "Hello section"


class _WorldModule(PromptModule):
    id = "world"

    def render(self, context, state):
        return "World section"


class _DisabledModule(PromptModule):
    id = "disabled"

    def enabled(self, context, state):
        return False

    def render(self, context, state):
        return "Should not appear"


class TestPromptComposer:
    def test_compose_in_order(self):
        composer = PromptComposer([_HelloModule(), _WorldModule()])
        ctx = type("Ctx", (), {"prompt": "make a page"})()
        state = type("State", (), {})()
        messages = composer.compose(ctx, state)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Hello section" in messages[0]["content"]
        assert "World section" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "make a page"

    def test_disabled_module_skipped(self):
        composer = PromptComposer([_HelloModule(), _DisabledModule(), _WorldModule()])
        ctx = type("Ctx", (), {"prompt": "test"})()
        state = type("State", (), {})()
        messages = composer.compose(ctx, state)
        assert "Should not appear" not in messages[0]["content"]


class TestPromptModuleRegistry:
    def test_register_and_ordered(self):
        registry = PromptModuleRegistry()
        registry.register(_WorldModule())
        registry.register(_HelloModule())
        modules = registry.ordered_modules()
        assert modules[0].id == "world"
        assert modules[1].id == "hello"

    def test_duplicate_raises(self):
        registry = PromptModuleRegistry()
        registry.register(_HelloModule())
        with pytest.raises(ValueError, match="Duplicate"):
            registry.register(_HelloModule())

    def test_get_not_found(self):
        registry = PromptModuleRegistry()
        with pytest.raises(KeyError):
            registry.get("missing")
