from app.agent_loop.prompts.implement import IMPLEMENT_MODE_SYSTEM_PROMPT
from app.agent_loop.prompts.plan import PLAN_MODE_SYSTEM_PROMPT
from app.runtime.event_bus import EventBus
from app.runtime.orchestrator import RuntimeOrchestrator


def test_agent_loop_registry_excludes_conversation_content_modules():
    services = RuntimeOrchestrator()._build_services(EventBus(agent_run_id=1))
    module_ids = [
        module.id for module in services.prompt_module_registry.ordered_modules()
    ]

    assert "chat_history_summary" not in module_ids
    assert "user_prompt" not in module_ids


def test_fallback_prompts_do_not_embed_current_user_prompt():
    assert "{user_prompt}" not in PLAN_MODE_SYSTEM_PROMPT
    assert "{user_prompt}" not in IMPLEMENT_MODE_SYSTEM_PROMPT
