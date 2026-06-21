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


class TestAgentLoopPromptBoundary:
    """验证 Agent Loop 的 System Prompt 不包含聊天历史和用户需求正文"""

    def test_agent_loop_registry_excludes_conversation_content_modules(self):
        from app.runtime.event_bus import EventBus
        from app.runtime.orchestrator import RuntimeOrchestrator

        services = RuntimeOrchestrator()._build_services(EventBus(agent_run_id=1))
        module_ids = [m.id for m in services.prompt_module_registry.ordered_modules()]

        assert "chat_history_summary" not in module_ids
        assert "user_prompt" not in module_ids

    def test_profile_prompts_do_not_embed_current_user_prompt(self):
        from app.prompts.profiles import PROMPT_PROFILES

        for profile_name, module_ids in PROMPT_PROFILES.items():
            for module_id in module_ids:
                assert "{user_prompt}" not in module_id, (
                    f"Profile {profile_name} module {module_id} 不应包含 {{user_prompt}} 占位符"
                )
