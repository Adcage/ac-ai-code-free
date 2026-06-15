import logging
from pathlib import Path
from typing import Any

from app.capabilities.common.asset_index import AssetIndex
from app.capabilities.common.capability_selection import CapabilitySelection
from app.capabilities.common.loader_result import SelectedCapabilities
from app.capabilities.craft.selector import CraftSelector
from app.capabilities.design_systems.selector import DesignSystemSelector
from app.capabilities.seeds.applier import SeedApplier
from app.capabilities.seeds.selector import SeedSelector
from app.capabilities.skills.selector import SkillSelector
from app.capabilities.templates.selector import TemplateSelector
from app.core.error_codes import AgentErrorCode
from app.core.exceptions import AgentRuntimeError
from app.nodes.base import NodeMetadata, RuntimeNode
from app.runtime.context import ExecutionContext, RunMode
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.state import ExecutionState
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.nodes.select_capabilities")


class SelectCapabilitiesNode(RuntimeNode):
    metadata = NodeMetadata(
        id="select_capabilities",
        name="选择能力",
        description="根据提示词和上下文选择技能、种子、模板、设计系统和工艺规则",
    )

    def __init__(self) -> None:
        self._skill_selector = SkillSelector()
        self._design_system_selector = DesignSystemSelector()
        self._seed_selector = SeedSelector()
        self._seed_applier = SeedApplier()
        self._template_selector = TemplateSelector()
        self._craft_selector = CraftSelector()

    async def run(
        self,
        context: ExecutionContext,
        state: ExecutionState,
        services: RuntimeServices,
    ) -> ExecutionState:
        asset_manager = services.asset_manager
        if asset_manager is None:
            raise AgentRuntimeError(
                "AssetManager 未注入 RuntimeServices",
                code=AgentErrorCode.STATE_ERROR,
            )

        index: AssetIndex = asset_manager.get_index()
        prompt = context.prompt
        code_gen_type = context.code_gen_type.value
        run_mode = context.run_mode.value

        skills = self._skill_selector.select(prompt, index.skill_registry)
        skill = skills[0] if skills else None
        logger.info(
            "skill selected | count=%d first_id=%s", len(skills), skill.id if skill else "none"
        )

        design_system = self._design_system_selector.select(
            prompt, code_gen_type, skill, index.design_system_registry
        )
        logger.info("design_system selected | id=%s", design_system.id if design_system else "none")

        recommended_seed_ids = skill.recommended_seeds if skill else ()
        seed = self._seed_selector.select(
            prompt,
            code_gen_type,
            run_mode,
            index.seed_registry,
            recommended_seed_ids=recommended_seed_ids,
        )
        logger.info("seed selected | id=%s", seed.id if seed else "none")

        if seed is not None:
            workspace_path = Path(context.workspace_path)
            try:
                self._seed_applier.apply(seed, workspace_path)
            except Exception as e:
                if context.run_mode == RunMode.GENERATE:
                    raise AgentRuntimeError(
                        f"Seed 文件复制失败 (generate 模式关键错误): {e}",
                        code=AgentErrorCode.STATE_ERROR,
                    )
                logger.warning("seed apply failed (non-generate mode, continuing): %s", e)

        recommended_template_ids = skill.related_templates if skill else ()
        template = None
        try:
            template = self._template_selector.select(
                prompt,
                code_gen_type,
                skill.id if skill else None,
                index.template_registry,
                recommended_template_ids=recommended_template_ids,
            )
        except Exception as e:
            logger.warning("template selection failed, skipping: %s", e)
        logger.info("template selected | id=%s", template.id if template else "none")

        required_craft_ids: tuple[str, ...] = ()
        if skill is not None and skill.craft.requires:
            required_craft_ids = skill.craft.requires

        suggested_craft_ids: tuple[str, ...] = ()
        if design_system is not None and design_system.suggested_craft:
            suggested_craft_ids = design_system.suggested_craft

        default_craft_ids = self._default_craft_ids(code_gen_type, index.manifest)

        craft = self._craft_selector.select(
            code_gen_type,
            index.craft_registry,
            required_craft_ids=required_craft_ids,
            suggested_craft_ids=suggested_craft_ids,
            default_craft_ids=default_craft_ids,
            aliases=index.manifest.aliases.get("craft", {}),
        )
        logger.info("craft selected | count=%d ids=%s", len(craft), [c.id for c in craft])

        selection = CapabilitySelection(
            skill_ids=tuple(s.id for s in skills),
            seed_id=seed.id if seed else "",
            template_ids=(template.id,) if template else (),
            design_system_id=design_system.id if design_system else "",
            craft_ids=tuple(c.id for c in craft),
            project_mode=code_gen_type,
            selection_source="selector",
        )
        selected_capabilities = SelectedCapabilities(
            selection=selection,
            skills=list(skills),
            seed=seed,
            templates=[template] if template else [],
            design_system=design_system,
            craft=list(craft),
        )

        state.selected_capabilities = selected_capabilities
        state.selected_skill_id = skill.id if skill else ""
        state.selected_seed_id = seed.id if seed else ""
        state.selected_template_id = template.id if template else ""
        state.selected_design_system_id = design_system.id if design_system else ""
        state.selected_craft_ids = [c.id for c in craft]
        state.capability_selection = selection
        state.selection_source = selection.selection_source

        await services.event_bus.emit(
            RuntimeEvent(
                RuntimeEventType.CAPABILITY_SELECTED,
                {
                    "selection_source": selection.selection_source,
                    "skill_ids": list(selection.skill_ids),
                    "seed_id": selection.seed_id,
                    "template_ids": list(selection.template_ids),
                    "design_system_id": selection.design_system_id,
                    "craft_ids": list(selection.craft_ids),
                    "project_mode": selection.project_mode,
                    "reason": selection.reason,
                },
            )
        )

        await services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.NODE_COMPLETED, {"node_id": "select_capabilities"})
        )

        return state

    def _default_craft_ids(self, code_gen_type: str, manifest: Any) -> tuple[str, ...]:
        defaults = manifest.defaults.get(code_gen_type, {})
        craft = defaults.get("craft", ())
        if isinstance(craft, list):
            return tuple(str(c) for c in craft)
        return ()
