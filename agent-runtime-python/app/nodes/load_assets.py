import logging

from app.capabilities.common.asset_index import AssetIndex
from app.core.error_codes import AgentErrorCode
from app.core.exceptions import AgentRuntimeError
from app.nodes.base import NodeMetadata, RuntimeNode
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.state import ExecutionState
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.nodes.load_assets")


class LoadAssetsNode(RuntimeNode):
    metadata = NodeMetadata(id="load_assets", name="加载资产", description="从文件系统加载技能、种子、模板、设计系统和工艺规则资产")

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

        try:
            index: AssetIndex = asset_manager.get_index()
        except Exception as e:
            raise AgentRuntimeError(
                f"资产索引加载失败: {e}",
                code=AgentErrorCode.STATE_ERROR,
            )

        state.asset_counts = {
            "skills": len(index.skill_registry.all()),
            "seeds": len(index.seed_registry.all()),
            "templates": len(index.template_registry.all()),
            "design_systems": len(index.design_system_registry.all()),
            "crafts": len(index.craft_registry.all()),
        }

        logger.info(
            "load_assets done | skills=%d seeds=%d templates=%d design_systems=%d crafts=%d",
            state.asset_counts["skills"],
            state.asset_counts["seeds"],
            state.asset_counts["templates"],
            state.asset_counts["design_systems"],
            state.asset_counts["crafts"],
        )

        await services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.NODE_COMPLETED, {"node_id": "load_assets"})
        )

        return state
