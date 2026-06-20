import logging

from app.nodes.base import NodeMetadata, RuntimeNode
from app.runtime.context import ExecutionContext
from app.runtime.state import ExecutionState
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.nodes.compose_prompt")


class ComposePromptNode(RuntimeNode):
    metadata = NodeMetadata(
        id="compose_prompt", name="提示词组合", description="组合系统提示词和用户提示词"
    )

    async def run(
        self,
        context: ExecutionContext,
        state: ExecutionState,
        services: RuntimeServices,
    ) -> ExecutionState:
        composer = services.prompt_composer
        if composer is None:
            from app.prompts.composer import PromptComposer

            composer = PromptComposer()

        if services.prompt_module_registry is not None:
            composer = PromptComposer(modules=services.prompt_module_registry.ordered_modules())

        state.prompt_messages = composer.compose(context, state)
        logger.info(
            "compose_prompt | messages=%d systemLen=%d",
            len(state.prompt_messages),
            len(state.prompt_messages[0]["content"]) if state.prompt_messages else 0,
        )
        return state
