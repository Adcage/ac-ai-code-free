from app.agent_loop.state import AgentLoopState
from app.prompts.loop_modules import SkillContextModule
from app.runtime.event_bus import EventBus
from app.runtime.orchestrator import RuntimeOrchestrator


def test_agent_loop_registry_excludes_conversation_content_modules():
    services = RuntimeOrchestrator()._build_services(EventBus(agent_run_id=1))
    module_ids = [
        module.id for module in services.prompt_module_registry.ordered_modules()
    ]

    assert "chat_history_summary" not in module_ids
    assert "user_prompt" not in module_ids


def test_plan_workflow_does_not_use_hardcoded_tool_signatures():
    from app.prompts.loop_modules import PlanWorkflowModule

    module = PlanWorkflowModule()
    rendered = module.render(None, AgentLoopState(mode="plan"))

    assert "write_file" not in rendered
    assert "switch_mode" not in rendered
    assert "ask_user(" not in rendered
    assert "write_plan(" not in rendered


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

    from app.prompts.composer import PromptComposer

    messages = PromptComposer([SkillContextModule()]).compose(None, state)

    assert messages
    assert "可用 Skill 列表" in messages[0]["content"]
    assert "ui-ux-pro-max" in messages[0]["content"]
