import logging

from app.nodes.base import NodeMetadata, RuntimeNode
from app.runtime.context import ExecutionContext, RunMode
from app.runtime.state import ExecutionState
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.nodes.classify_task")


class ClassifyTaskNode(RuntimeNode):
    metadata = NodeMetadata(id="classify_task", name="任务分类", description="识别任务类型")

    async def run(
        self,
        context: ExecutionContext,
        state: ExecutionState,
        services: RuntimeServices,
    ) -> ExecutionState:
        if context.run_mode == RunMode.MODIFY:
            state.task_type = "modify"
        elif context.run_mode == RunMode.ROUTE:
            state.task_type = "route"
        else:
            state.task_type = "generate"

        logger.info("classify_task | taskType=%s", state.task_type)
        return state
