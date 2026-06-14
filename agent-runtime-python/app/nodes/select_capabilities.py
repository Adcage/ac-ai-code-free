import logging
from pathlib import Path

from app.capabilities.common.asset_index import AssetIndex
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
        id="select_capabilities", name="选择能力", description="根据提示词和上下文选择技能、种子、模板、设计系统和工艺规则"
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

        skill = self._skill_selector.select(prompt, index.skill_registry)
        logger.info("skill selected | id=%s", skill.id if skill else "none")

        design_system = self._design_system_selector.select(
            prompt, code_gen_type, skill, index.design_system_registry
        )
        logger.info("design_system selected | id=%s", design_system.id if design_system else "none")

        seed = self._seed_selector.select(
            prompt, code_gen_type, run_mode, index.seed_registry
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

        template = None
        try:
            template = self._template_selector.select(
                prompt, code_gen_type, skill.id if skill else None, index.template_registry
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

        craft = self._craft_selector.select(
            code_gen_type, index.craft_registry,
            required_craft_ids=required_craft_ids,
            suggested_craft_ids=suggested_craft_ids,
        )
        logger.info("craft selected | count=%d ids=%s", len(craft), [c.id for c in craft])

        selected_capabilities = SelectedCapabilities(
            skill=skill,
            seed=seed,
            template=template,
            design_system=design_system,
            craft=list(craft),
        )

        state.selected_capabilities = selected_capabilities
        state.selected_skill_id = skill.id if skill else ""
        state.selected_seed_id = seed.id if seed else ""
        state.selected_template_id = template.id if template else ""
        state.selected_design_system_id = design_system.id if design_system else ""
        state.selected_craft_ids = [c.id for c in craft]

        await services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.NODE_COMPLETED, {"node_id": "select_capabilities"})
        )

        return state
