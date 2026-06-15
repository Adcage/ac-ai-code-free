from pathlib import Path
from unittest.mock import MagicMock

import asyncio

import pytest

from app.capabilities.common.asset_index import AssetIndex, AssetManager
from app.capabilities.craft.registry import CraftRegistry
from app.capabilities.craft.types import CraftDefinition
from app.capabilities.design_systems.registry import DesignSystemRegistry
from app.capabilities.design_systems.types import DesignSystemDefinition, DesignSystemFiles
from app.capabilities.seeds.registry import SeedRegistry
from app.capabilities.seeds.types import SeedDefinition
from app.capabilities.skills.registry import SkillRegistry
from app.capabilities.skills.types import (
    SkillCraftRequirement,
    SkillDefinition,
    SkillDesignSystemRequirement,
    SkillPreview,
)
from app.capabilities.templates.registry import TemplateRegistry
from app.capabilities.templates.types import TemplateDefinition
from app.nodes.select_capabilities import SelectCapabilitiesNode
from app.runtime.context import CodeGenType, ExecutionContext, RunMode
from app.runtime.event_bus import EventBus
from app.runtime.events import RuntimeEventType
from app.runtime.services import RuntimeServices
from app.runtime.state import ExecutionState


def _make_asset_index_with_recommended() -> AssetIndex:
    skill_reg = SkillRegistry()
    skill_reg.register(
        SkillDefinition(
            id="dashboard",
            name="dashboard",
            description="Dashboard skill",
            triggers=("dashboard", "后台"),
            mode="prototype",
            platform="desktop",
            scenario="operations",
            preview=SkillPreview(type="html", entry="index.html"),
            design_system=SkillDesignSystemRequirement(requires=True),
            craft=SkillCraftRequirement(requires=("state-coverage",)),
            body="Build a dashboard.",
            source_path=Path("."),
            target_code_gen_types=("single_file", "multi_file", "vue_project"),
            related_templates=("dashboard",),
            recommended_seeds=("vue-dashboard",),
        )
    )

    ds_reg = DesignSystemRegistry()
    ds_reg.register(
        DesignSystemDefinition(
            id="ant",
            name="Ant",
            category="corporate",
            description="Ant design system",
            import_mode="normalized",
            files=DesignSystemFiles(design=Path("/tmp/DESIGN.md")),
            suggested_craft=("anti-ai-slop",),
            source_path=Path("."),
        )
    )

    seed_reg = SeedRegistry()
    seed_reg.register(
        SeedDefinition(
            id="vue-basic",
            name="Vue Basic",
            description="Basic Vue seed",
            code_gen_type="vue_project",
            triggers=("vue",),
            entry="src/App.vue",
            files_dir=Path("/tmp/seed-files"),
            copy_mode="missing-only",
            source_path=Path("."),
        )
    )
    seed_reg.register(
        SeedDefinition(
            id="vue-dashboard",
            name="Vue Dashboard",
            description="Vue dashboard seed",
            code_gen_type="vue_project",
            triggers=("dashboard",),
            entry="src/App.vue",
            files_dir=Path("/tmp/dashboard-seed-files"),
            copy_mode="missing-only",
            source_path=Path("."),
        )
    )

    template_reg = TemplateRegistry()
    template_reg.register(
        TemplateDefinition(
            id="dashboard",
            name="Dashboard",
            description="Dashboard template",
            code_gen_type="vue_project",
            triggers=("dashboard",),
            entry="src/App.vue",
            max_prompt_files=1,
            files=(Path("files/src/App.vue"),),
            source_path=Path("."),
        )
    )

    craft_reg = CraftRegistry()
    craft_reg.register(
        CraftDefinition(
            id="anti-ai-slop",
            name="Anti AI Slop",
            description="Anti slop rules",
            applies_to=(),
            priority=50,
            body="No lorem ipsum.",
            source_path=Path("."),
        )
    )
    craft_reg.register(
        CraftDefinition(
            id="state-coverage",
            name="State Coverage",
            description="State coverage rules",
            applies_to=(),
            priority=60,
            body="Include loading states.",
            source_path=Path("."),
        )
    )

    return AssetIndex(
        skill_registry=skill_reg,
        seed_registry=seed_reg,
        template_registry=template_reg,
        design_system_registry=ds_reg,
        craft_registry=craft_reg,
    )


def _make_context(
    prompt: str = "生成一个后台数据看板",
    code_gen_type: CodeGenType = CodeGenType.VUE_PROJECT,
    run_mode: RunMode = RunMode.GENERATE,
    workspace_path: str = "/tmp/workspace",
) -> ExecutionContext:
    return ExecutionContext(
        agent_run_id=1,
        app_id=1,
        session_id=1,
        user_id=1,
        prompt=prompt,
        code_gen_type=code_gen_type,
        workspace_path=workspace_path,
        run_mode=run_mode,
    )


def _make_services(asset_manager: AssetManager | None = None) -> RuntimeServices:
    event_bus = EventBus(agent_run_id=1)
    return RuntimeServices(
        asset_manager=asset_manager,
        event_bus=event_bus,
    )


class TestSelectCapabilitiesNode:
    @pytest.mark.asyncio
    async def test_select_capabilities_records_selection_source_and_multiple_assets(
        self, tmp_path: Path
    ):
        index = _make_asset_index_with_recommended()

        mock_manager = MagicMock(spec=AssetManager)
        mock_manager.get_index.return_value = index

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        services = _make_services(asset_manager=mock_manager)
        state = ExecutionState()
        context = _make_context(workspace_path=str(workspace))

        node = SelectCapabilitiesNode()
        result = await node.run(context, state, services)

        assert result.capability_selection is not None
        assert result.selection_source == "selector"
        assert result.capability_selection.skill_ids == ("dashboard",)
        assert result.capability_selection.seed_id == "vue-dashboard"
        assert result.capability_selection.template_ids == ("dashboard",)
        assert result.capability_selection.design_system_id == "ant"
        assert "anti-ai-slop" in result.capability_selection.craft_ids
        assert "state-coverage" in result.capability_selection.craft_ids
        assert result.selected_capabilities.skill.id == "dashboard"
        assert result.selected_capabilities.template.id == "dashboard"

    @pytest.mark.asyncio
    async def test_node_emits_completed_event(self, tmp_path: Path):
        index = _make_asset_index_with_recommended()

        mock_manager = MagicMock(spec=AssetManager)
        mock_manager.get_index.return_value = index

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        services = _make_services(asset_manager=mock_manager)
        state = ExecutionState()
        context = _make_context(workspace_path=str(workspace))

        node = SelectCapabilitiesNode()
        await node.run(context, state, services)

        events = []
        for _ in range(10):
            try:
                event = await asyncio.wait_for(services.event_bus.next_event(), timeout=1.0)
            except asyncio.TimeoutError:
                break
            if event is None:
                break
            events.append(event)
            if any(
                e.event.event_type == RuntimeEventType.CAPABILITY_SELECTED for e in events
            ) and any(e.event.event_type == RuntimeEventType.NODE_COMPLETED for e in events):
                break

        assert any(e.event.event_type == RuntimeEventType.CAPABILITY_SELECTED for e in events)
        assert any(e.event.event_type == RuntimeEventType.NODE_COMPLETED for e in events)
