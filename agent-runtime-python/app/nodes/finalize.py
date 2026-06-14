import logging

from app.nodes.base import NodeMetadata, RuntimeNode
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.state import ExecutionState
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.nodes.finalize")


class FinalizeNode(RuntimeNode):
    metadata = NodeMetadata(id="finalize", name="完成处理", description="汇总运行结果并上报平台")

    async def run(
        self,
        context: ExecutionContext,
        state: ExecutionState,
        services: RuntimeServices,
    ) -> ExecutionState:
        success = len(state.errors) == 0
        summary_parts = []
        if state.model_response_text:
            summary_parts.append(f"模型输出 {len(state.model_response_text)} 字")
        if state.files_touched:
            summary_parts.append(f"写入 {len(state.files_touched)} 个文件")
        if state.executed_tool_calls:
            summary_parts.append(f"执行 {len(state.executed_tool_calls)} 次工具调用")
        if state.errors:
            summary_parts.append(f"发生 {len(state.errors)} 个错误")

        state.final_summary = "，".join(summary_parts) if summary_parts else "无操作"

        if services.platform_client is not None:
            try:
                latency_ms = sum(r.latency_ms for r in state.node_results)
                await services.platform_client.complete_agent_run(
                    agent_run_id=context.agent_run_id,
                    success=success,
                    workspace_path=context.workspace_path,
                    latency_ms=latency_ms,
                    error_message="; ".join(state.errors) if state.errors else "",
                )
                logger.info("complete_agent_run | success=%s latency_ms=%d", success, latency_ms)
            except Exception as e:
                logger.error("complete_agent_run failed: %s", e, exc_info=True)
                state.errors.append(f"上报运行结果失败: {e}")

        done_message = state.final_summary if success else f"运行失败: {'; '.join(state.errors)}"
        await services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.DONE, {"message": done_message})
        )

        logger.info("finalize | success=%s summary=%s", success, state.final_summary)
        return state
