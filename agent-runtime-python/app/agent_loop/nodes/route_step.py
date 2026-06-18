import logging

from langchain_core.tools import BaseTool

from app.agent_loop.nodes.step_base import (
    _build_tool_handlers,
    _execute_single_step,
    _format_tool_list,
)
from app.agent_loop.state import AgentLoopState
from app.agent_loop.tools.ask_user import AskUserTool
from app.agent_loop.tools.decide_route import DecideRouteTool
from app.prompts.composer import PromptComposer
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.services import RuntimeServices
from app.tools.file_tools import Workspace, FileTools
from app.tools.langchain_tools import create_file_tools

logger = logging.getLogger("app.agent_loop.nodes.route_step")


class RouteStepNode:
    """统一路由决策节点，在大循环外和大循环内都会被调用。
    三套互斥提示词模块：route_initial / route_after_implement / route_after_validate。"""

    def __init__(self, context: ExecutionContext, services: RuntimeServices):
        self._context = context
        self._services = services

    async def __call__(self, state: AgentLoopState) -> AgentLoopState:
        # 恢复状态时跳过路由
        if state.route_decided and state.iteration > 0:
            return state

        # 超过步数上限，按默认规则路由
        if state.route_iterations >= state.max_route_iterations:
            self._apply_default_route(state)
            return state

        await self._services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.STATUS, {"message": "Route step"})
        )

        # 构建只读工具集
        workspace = Workspace(self._context.workspace_path)
        file_tools = FileTools(workspace)
        file_lc_tools = create_file_tools(file_tools)

        # 构建 loop 工具
        decide_route = DecideRouteTool()
        decide_route.set_state(state)
        ask_user = AskUserTool()
        ask_user.set_state(state)
        ask_user.set_event_bus(self._services.event_bus)

        lc_tools: list[BaseTool] = list(file_lc_tools) + [decide_route, ask_user]
        tool_handlers = _build_tool_handlers(file_tools, None)

        # 构建系统提示词
        system_prompt = self._compose_prompt(state, lc_tools)

        state.route_iterations += 1
        logger.info(
            "route_step | route_iterations=%d mode=%s route_decided=%s",
            state.route_iterations,
            state.mode,
            state.route_decided,
        )

        result = await _execute_single_step(
            state,
            self._context,
            self._services,
            system_prompt,
            lc_tools,
            tool_handlers,
            file_tools,
        )

        # route_step 完成后重置阶段标记（已被消费）
        if result.route_decided:
            result.implement_just_finished = False
            result.validate_just_finished = False

        return result

    def _compose_prompt(self, state: AgentLoopState, lc_tools: list[BaseTool]) -> str:
        registry = getattr(self._services, "prompt_module_registry", None)
        if registry is not None:
            # 注入工具列表到 ToolListModule
            tool_list_module = registry.get_by_id("tool_list")
            if tool_list_module is not None:
                tool_list_module.set_tools(lc_tools)

            composer = PromptComposer(registry.ordered_modules())
            messages = composer.compose(self._context, state)
            if messages and messages[0].get("role") == "system":
                return messages[0]["content"]

        # 回退：简单默认提示词
        return (
            "你需要判断当前请求应该进入哪种模式。\n\n"
            "## 可用工具\n\n"
            + _format_tool_list(lc_tools)
            + "\n\n调用 `decide_route` 输出你的路由决策。"
        )

    def _apply_default_route(self, state: AgentLoopState) -> None:
        """超过步数上限时的保守默认路由。"""
        if not state.route_decided:
            # 首次路由默认进 plan
            state.route_decided = True
            state.route_decision = {"mode": "plan", "code_gen_type": "", "reason": "默认路由"}
            state.mode = "plan"
        elif state.implement_just_finished:
            # implement 后默认进 validate（保守策略）
            state.route_decided = True
            state.route_decision = {"mode": "validate", "code_gen_type": "", "reason": "默认路由"}
            state.mode = "validate"
        elif state.validate_just_finished:
            # validate 后默认 finish
            state.route_decided = True
            state.route_decision = {"mode": "finish", "code_gen_type": "", "reason": "默认路由"}
        logger.warning("route_step | exceeded max_route_iterations, applied default route: %s", state.route_decision)
