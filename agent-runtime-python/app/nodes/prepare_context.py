import logging

from app.nodes.base import NodeMetadata, RuntimeNode
from app.runtime.context import ExecutionContext
from app.runtime.state import ExecutionState
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.nodes.prepare_context")


class PrepareContextNode(RuntimeNode):
    metadata = NodeMetadata(
        id="prepare_context", name="准备上下文", description="校验运行上下文完整性"
    )

    def can_run(self, context: ExecutionContext, state: ExecutionState) -> bool:
        return True

    async def run(
        self,
        context: ExecutionContext,
        state: ExecutionState,
        services: RuntimeServices,
    ) -> ExecutionState:
        if not context.prompt or not context.prompt.strip():
            from app.core.error_codes import AgentErrorCode
            from app.core.exceptions import AgentRuntimeError

            raise AgentRuntimeError("提示词不能为空", code=AgentErrorCode.PROMPT_EMPTY)

        if context.app_id <= 0:
            logger.warning("app_id is invalid: %s", context.app_id)

        if context.session_id <= 0:
            logger.warning("session_id is invalid: %s", context.session_id)

        if context.run_mode == "modify" and not context.original_content:
            logger.warning("modify mode without original_content")

        state.task_type = context.run_mode.value
        logger.info(
            "prepare_context done | app=%s session=%s runMode=%s",
            context.app_id,
            context.session_id,
            context.run_mode.value,
        )
        return state
