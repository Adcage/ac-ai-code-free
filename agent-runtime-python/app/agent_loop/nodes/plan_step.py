import logging

from langchain_core.tools import BaseTool

from app.agent_loop.nodes.step_base import (
    _build_tool_handlers,
    _create_terminal_tools_for_mode,
    _execute_single_step,
    _format_tool_list,
    _get_skill_dir,
    _make_loop_tools,
)
from app.agent_loop.prompts.plan import PLAN_MODE_SYSTEM_PROMPT
from app.agent_loop.prompts.implement import IMPLEMENT_MODE_SYSTEM_PROMPT
from app.agent_loop.prompts.plan_spec import PLAN_SPEC
from app.agent_loop.state import AgentLoopState
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.services import RuntimeServices
from app.tools.file_tools import Workspace, FileTools
from app.tools.langchain_tools import create_file_tools

logger = logging.getLogger("app.agent_loop.nodes.plan_step")


class PlanStepNode:
    def __init__(self, context: ExecutionContext, services: RuntimeServices):
        self._context = context
        self._services = services

    async def __call__(self, state: AgentLoopState) -> AgentLoopState:
        await self._services.event_bus.emit(
            RuntimeEvent(RuntimeEventType.STATUS, {"message": f"Plan step {state.iteration + 1}"})
        )

        workspace = Workspace(self._context.workspace_path)
        skill_dir = _get_skill_dir(state)
        file_tools = FileTools(workspace, skill_dir=skill_dir)

        terminal_tools = _create_terminal_tools_for_mode(workspace, readonly=True)

        file_lc_tools = create_file_tools(file_tools)
        lc_tools: list[BaseTool] = list(file_lc_tools)
        if terminal_tools is not None:
            from app.tools.langchain_tools import RunCommandTool

            cmd_tool = RunCommandTool(terminal_tools=terminal_tools)
            cmd_tool.description = "在项目工作区执行预授权终端命令。plan 模式下仅限只读命令（ls、cat、git status 等）。"
            lc_tools.append(cmd_tool)

        lc_tools.extend(_make_loop_tools(state, self._services.event_bus))

        tool_handlers = _build_tool_handlers(file_tools, terminal_tools)
        tool_handlers.pop("write_file", None)

        system_prompt = PLAN_MODE_SYSTEM_PROMPT.format(
            tool_list=_format_tool_list(lc_tools),
            user_prompt=self._context.prompt,
            plan_spec=PLAN_SPEC,
        )

        caps_text = ""
        if state.selected_capabilities and getattr(state.selected_capabilities, "skill", None):
            caps_text = f"\n\n## 已选择的 Skill\n\n{state.selected_capabilities.skill.name}: {state.selected_capabilities.skill.description}"
        else:
            index = getattr(state, "_asset_index", None)
            if index is not None:
                skills = index.skill_registry.all()
                if skills:
                    caps_text = "\n\n## 可用 Skill 列表\n\n你可以使用 `select_skill(skill_id, reason)` 选择一个适合当前任务的 Skill。\n\n"
                    for s in skills:
                        caps_text += f"- **{s.id}**: {s.description}\n"

        system_prompt += caps_text

        state.plan_iterations += 1
        logger.info(
            "plan_step | iteration=%d plan_iterations=%d mode=%s",
            state.iteration + 1,
            state.plan_iterations,
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


class ImplementStepNode:
    def __init__(self, context: ExecutionContext, services: RuntimeServices):
        self._context = context
        self._services = services

    async def __call__(self, state: AgentLoopState) -> AgentLoopState:
        await self._services.event_bus.emit(
            RuntimeEvent(
                RuntimeEventType.STATUS, {"message": f"Implement step {state.iteration + 1}"}
            )
        )

        workspace = Workspace(self._context.workspace_path)
        skill_dir = _get_skill_dir(state)
        file_tools = FileTools(workspace, skill_dir=skill_dir)

        terminal_tools = _create_terminal_tools_for_mode(workspace, readonly=False)

        from app.tools.langchain_tools import create_all_tools

        lc_tools: list[BaseTool] = create_all_tools(file_tools, terminal_tools=terminal_tools)
        lc_tools.extend(_make_loop_tools(state, self._services.event_bus))

        tool_handlers = _build_tool_handlers(file_tools, terminal_tools)

        outline_text = "暂无实现规划"
        if state.implementation_outline:
            if isinstance(state.implementation_outline, dict):
                outline_text = state.implementation_outline.get("text", str(state.implementation_outline))
            else:
                outline_text = str(state.implementation_outline)

        system_prompt = IMPLEMENT_MODE_SYSTEM_PROMPT.format(
            tool_list=_format_tool_list(lc_tools),
            user_prompt=self._context.prompt,
            implementation_outline=outline_text,
        )

        if state.selected_capabilities and getattr(state.selected_capabilities, "skill", None):
            skill = state.selected_capabilities.skill
            skill_text = f"\n\n## 已选择的 Skill\n\n**{skill.name}** (ID: {skill.id}): {skill.description}\n\n你可以用 `read_file(scope='skill', relative_path='SKILL.md')` 读取 Skill 的详细规则和参考资源。"
            system_prompt += skill_text

        logger.info("implement_step | iteration=%d mode=%s", state.iteration + 1, state.mode)

        return await _execute_single_step(
            state,
            self._context,
            self._services,
            system_prompt,
            lc_tools,
            tool_handlers,
            file_tools,
        )
