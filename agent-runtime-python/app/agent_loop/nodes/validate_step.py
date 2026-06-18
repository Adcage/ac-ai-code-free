import logging

from langchain_core.tools import BaseTool

from app.agent_loop.nodes.step_base import (
    _build_tool_handlers,
    _execute_single_step,
    _format_tool_list,
)
from app.agent_loop.state import AgentLoopState
from app.agent_loop.tools.decide_validation import DecideValidationTool
from app.agent_loop.tools.run_checks import RunChecksTool
from app.prompts.composer import PromptComposer
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.services import RuntimeServices
from app.tools.file_tools import Workspace, FileTools
from app.tools.langchain_tools import create_file_tools

logger = logging.getLogger("app.agent_loop.nodes.validate_step")


class ValidateStepNode:
    """校验模式节点，和 plan/implement 同级别的大循环模式。
    AI 自主调用工具校验代码质量，然后调用 decide_validation 输出结论。"""

    def __init__(self, context: ExecutionContext, services: RuntimeServices):
        self._context = context
        self._services = services

    async def __call__(self, state: AgentLoopState) -> AgentLoopState:
        # 超过校验上限，按保守策略处理
        if state.validate_iterations >= state.max_validate_iterations:
            if state.validation_status == "failed":
                state.mode = "implement"
                state.implement_just_finished = False
                state.validate_just_finished = True
            else:
                state.validate_just_finished = True
            logger.warning(
                "validate_step | exceeded max_validate_iterations, status=%s",
                state.validation_status,
            )
            return state

        await self._services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.STATUS, {"message": f"Validate step {state.validate_iterations + 1}"})
        )

        workspace = Workspace(self._context.workspace_path)
        file_tools = FileTools(workspace)
        file_lc_tools = create_file_tools(file_tools)

        # 构建 validate 专用工具集
        run_checks = RunChecksTool()
        run_checks.set_state(state)
        run_checks.set_workspace(self._context.workspace_path)
        run_checks.set_quality_checker(self._services.quality_checker)

        decide_validation = DecideValidationTool()
        decide_validation.set_state(state)

        lc_tools = list(file_lc_tools) + [run_checks, decide_validation]
        tool_handlers = _build_tool_handlers(file_tools, None)

        # 构建系统提示词
        system_prompt = self._compose_prompt(state, lc_tools)

        logger.info(
            "validate_step | validate_iterations=%d mode=%s",
            state.validate_iterations + 1,
            state.mode,
        )

        return await _execute_single_step(
            state,
            self._context,
            self._services,
            system_prompt,
            lc_tools,
            tool_handlers,
            file_tools,
        )

    def _compose_prompt(self, state: AgentLoopState, lc_tools: list[BaseTool]) -> str:
        registry = getattr(self._services, "prompt_module_registry", None)
        if registry is not None:
            tool_list_module = registry.get_by_id("tool_list")
            if tool_list_module is not None:
                tool_list_module.set_tools(lc_tools)

            composer = PromptComposer(registry.ordered_modules())
            messages = composer.compose(self._context, state)
            if messages and messages[0].get("role") == "system":
                return messages[0]["content"]

        # 回退提示词
        return (
            "你处于校验模式。检查已生成的代码是否符合项目结构要求。\n\n"
            "1. 调用 `run_checks` 执行项目结构校验\n"
            "2. 综合判断后调用 `decide_validation` 输出结论\n\n"
            "## 可用工具\n\n"
            + _format_tool_list(lc_tools)
        )
