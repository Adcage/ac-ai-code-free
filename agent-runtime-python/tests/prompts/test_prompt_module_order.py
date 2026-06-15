from app.runtime.context import CodeGenType
from app.runtime.orchestrator import RuntimeOrchestrator


def test_prompt_module_order_places_assets_before_tool_and_output_contracts():
    orchestrator = RuntimeOrchestrator()
    registry = orchestrator._build_prompt_module_registry()
    module_ids = [module.id for module in registry.ordered_modules()]

    assert module_ids.index("selected_skill") < module_ids.index("tool_contract")
    assert module_ids.index("design_system") < module_ids.index("tool_contract")
    assert module_ids.index("craft_rules") < module_ids.index("artifact_output_contract")
    assert module_ids.index("artifact_output_contract") < module_ids.index("output_contract")
    assert module_ids[-1] == "anti_roleplay"


def test_artifact_output_contract_in_registry():
    orchestrator = RuntimeOrchestrator()
    registry = orchestrator._build_prompt_module_registry()
    module_ids = [module.id for module in registry.ordered_modules()]

    assert "artifact_output_contract" in module_ids


def test_artifact_output_contract_includes_mode_specific_rules():
    from app.prompts.asset_modules import ArtifactOutputContractModule

    module = ArtifactOutputContractModule()

    single = module.render(
        type("Context", (), {"code_gen_type": CodeGenType.SINGLE_FILE})(),
        None,
    )
    assert "single HTML file" in single
    assert "index.html" in single

    multi = module.render(
        type("Context", (), {"code_gen_type": CodeGenType.MULTI_FILE})(),
        None,
    )
    assert "multi-file HTML project" in multi
    assert "style.css" in multi

    vue = module.render(
        type("Context", (), {"code_gen_type": CodeGenType.VUE_PROJECT})(),
        None,
    )
    assert "Vue project" in vue
    assert "Vue SFC" in vue
