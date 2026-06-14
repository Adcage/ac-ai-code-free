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
        has_error_fail = any(
            r.get("status") == "fail" and r.get("severity") == "error"
            for r in state.quality_results
        )
        has_warnings = any(
            r.get("status") in ("warn", "fail") and r.get("severity") == "warning"
            for r in state.quality_results
        )

        success = len(state.errors) == 0 and not has_error_fail
        summary_parts = []
        if state.model_response_text:
            summary_parts.append(f"模型输出 {len(state.model_response_text)} 字")
        if state.files_touched:
            summary_parts.append(f"写入 {len(state.files_touched)} 个文件")
        if state.executed_tool_calls:
            summary_parts.append(f"执行 {len(state.executed_tool_calls)} 次工具调用")

        if state.artifact_manifest_path:
            summary_parts.append(f"Manifest: {state.artifact_manifest_path}")
        if state.selected_skill_id:
            summary_parts.append(f"Skill: {state.selected_skill_id}")
        if state.selected_design_system_id:
            summary_parts.append(f"Design System: {state.selected_design_system_id}")

        if state.quality_results:
            pass_count = sum(1 for r in state.quality_results if r.get("status") == "pass")
            warn_count = sum(1 for r in state.quality_results if r.get("status") == "warn")
            fail_count = sum(1 for r in state.quality_results if r.get("status") == "fail")
            summary_parts.append(f"质量检查: {pass_count} pass, {warn_count} warn, {fail_count} fail")
            if has_warnings and not has_error_fail:
                summary_parts.append("存在质量警告")

        if state.errors:
            summary_parts.append(f"发生 {len(state.errors)} 个错误")

        state.final_summary = "，".join(summary_parts) if summary_parts else "无操作"

        failed_checks = [
            r for r in state.quality_results
            if r.get("status") == "fail" and r.get("severity") == "error"
        ]
        error_message_parts = list(state.errors)
        if failed_checks:
            check_summary = "; ".join(
                f"{r.get('id', '?')}: {r.get('message', '')}" for r in failed_checks
            )
            error_message_parts.append(f"结构检查失败: {check_summary}")

        if services.platform_client is not None:
            try:
                latency_ms = sum(r.latency_ms for r in state.node_results)
                await services.platform_client.complete_agent_run(
                    agent_run_id=context.agent_run_id,
                    success=success,
                    workspace_path=context.workspace_path,
                    latency_ms=latency_ms,
                    error_message="; ".join(error_message_parts) if error_message_parts else "",
                )
                logger.info("complete_agent_run | success=%s latency_ms=%d", success, latency_ms)
            except Exception as e:
                logger.error("complete_agent_run failed: %s", e, exc_info=True)
                state.errors.append(f"上报运行结果失败: {e}")

        done_message = state.final_summary if success else f"运行失败: {'; '.join(error_message_parts)}"
        await services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.DONE, {"message": done_message})
        )

        logger.info("finalize | success=%s summary=%s", success, state.final_summary)
        return state
