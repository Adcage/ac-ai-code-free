import logging

from app.agent_loop.state import AgentLoopState
from app.capabilities.common.asset_index import AssetIndex
from app.modeling.roles import ModelRole
from app.runtime.context import ExecutionContext
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.agent_loop.nodes.init")


class InitNode:
    def __init__(self, context: ExecutionContext, services: RuntimeServices):
        self._context = context
        self._services = services

    async def __call__(self, state: AgentLoopState) -> AgentLoopState:
        state.mode = "plan"
        state.status = "running"

        asset_manager = self._services.asset_manager
        if asset_manager is not None:
            try:
                index: AssetIndex = asset_manager.get_index()
                state._asset_index = index
                logger.info(
                    "init | assets loaded: skills=%d seeds=%d templates=%d ds=%d crafts=%d",
                    len(index.skill_registry.all()),
                    len(index.seed_registry.all()),
                    len(index.template_registry.all()),
                    len(index.design_system_registry.all()),
                    len(index.craft_registry.all()),
                )
            except Exception as e:
                logger.warning("init | asset loading failed: %s", e)

        if self._services.model_resolver is not None:
            try:
                await self._services.model_resolver.load_bundle(self._context)
                model_config = self._services.model_resolver.resolve(ModelRole.PRIMARY)
                state.resolved_model = {
                    "provider": model_config.provider,
                    "modelName": model_config.model_name,
                    "baseUrl": model_config.base_url,
                    "apiKey": model_config.api_key,
                }
                logger.info(
                    "init | model resolved: %s/%s", model_config.provider, model_config.model_name
                )
            except Exception as e:
                logger.warning("init | model resolution failed: %s", e)

        return state
