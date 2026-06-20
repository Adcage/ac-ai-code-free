from app.agent_loop.prompts.implement import IMPLEMENT_MODE_SYSTEM_PROMPT
from app.agent_loop.prompts.plan import PLAN_MODE_SYSTEM_PROMPT
from app.agent_loop.state import AgentLoopState
from app.prompts.composer import PromptComposer
from app.prompts.loop_modules import PlanWorkflowModule, SkillContextModule
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


def test_plan_prompts_use_current_skill_resource_contract():
    module_prompt = PlanWorkflowModule().render(None, AgentLoopState(mode="plan"))

    assert "read_file(scope" not in PLAN_MODE_SYSTEM_PROMPT
    assert "read_file(scope" not in module_prompt
    assert "path=\"SKILL.md\"" not in PLAN_MODE_SYSTEM_PROMPT
    assert "path='SKILL.md'" not in module_prompt
    assert "read_asset(relative_path=" in PLAN_MODE_SYSTEM_PROMPT
    assert "read_asset(relative_path=" in module_prompt


def test_skill_context_module_lists_available_skills_before_selection():
    skill = type(
        "SkillDef",
        (),
        {"id": "ui-ux-pro-max", "description": "UI/UX design intelligence"},
    )()
    registry = type("SkillRegistry", (), {"all": lambda self: [skill]})()
    index = type("AssetIndex", (), {"skill_registry": registry})()
    state = AgentLoopState(mode="plan")
    state._asset_index = index

    messages = PromptComposer([SkillContextModule()]).compose(None, state)

    assert messages
    assert "可用 Skill 列表" in messages[0]["content"]
    assert "ui-ux-pro-max" in messages[0]["content"]
