import logging

from app.nodes.base import NodeMetadata, RuntimeNode
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.state import ExecutionState
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.nodes.resolve_model")


class ResolveModelNode(RuntimeNode):
    metadata = NodeMetadata(id="resolve_model", name="模型解析", description="根据角色解析模型配置")

    async def run(
        self,
        context: ExecutionContext,
        state: ExecutionState,
        services: RuntimeServices,
    ) -> ExecutionState:
        role = services.model_policy.role_for_node("call_model")
        state.selected_model_role = role

        if services.model_resolver is not None:
            await services.model_resolver.load_bundle(context)
            resolved = services.model_resolver.resolve(role)
            state.resolved_model = {
                "provider": resolved.provider,
                "modelName": resolved.model_name,
                "baseUrl": resolved.base_url,
                "apiKey": resolved.api_key,
                "modelConfigId": resolved.model_config_id,
                "configVersion": resolved.config_version,
                "source": resolved.source,
                "billingMode": resolved.billing_mode,
            }
        else:
            logger.warning("model_resolver not available in services")
            state.resolved_model = context.runtime_options.get("model_config")

        await services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.MODEL_SELECTED, {
                "role": role.value,
                "model": state.resolved_model.get("modelName", "") if state.resolved_model else "",
                "source": state.resolved_model.get("source", "") if state.resolved_model else "",
            })
        )

        logger.info("resolve_model | role=%s model=%s source=%s apiKeyLen=%d",
                     role.value,
                     state.resolved_model.get("modelName", "") if state.resolved_model else "none",
                     state.resolved_model.get("source", "") if state.resolved_model else "",
                     len(state.resolved_model.get("apiKey", "")) if state.resolved_model else 0)
        return state
