import logging

from langchain_core.tools import BaseTool

from app.agent_loop.nodes.step_base import (
    _build_tool_handlers,
    _create_terminal_tools_for_mode,
    _execute_single_step,
    _format_tool_list,
    _get_assets_dir,
    _get_skill_dir,
    _make_loop_tools,
)
from app.agent_loop.prompts.plan import PLAN_MODE_SYSTEM_PROMPT
from app.agent_loop.prompts.implement import IMPLEMENT_MODE_SYSTEM_PROMPT
from app.agent_loop.prompts.plan_spec import PLAN_SPEC
from app.agent_loop.state import AgentLoopState
from app.prompts.composer import PromptComposer
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.services import RuntimeServices
from app.tools.file_tools import Workspace, FileTools
from app.tools.langchain_tools import create_file_tools

logger = logging.getLogger("app.agent_loop.nodes.plan_step")


def _compose_system_prompt(
    state: AgentLoopState,
    context: ExecutionContext,
    services: RuntimeServices,
    lc_tools: list[BaseTool],
    fallback_prompt: str,
) -> str:
    """使用 PromptComposer 构建系统提示词，若 registry 不可用则回退到硬编码提示词。"""
    registry = getattr(services, "prompt_module_registry", None)
    if registry is None:
        return fallback_prompt

    # 注入工具列表到 ToolListModule
    tool_list_module = registry.get_by_id("tool_list")
    if tool_list_module is not None:
        tool_list_module.set_tools(lc_tools)

    composer = PromptComposer(registry.ordered_modules())
    messages = composer.compose(context, state)

    if messages and messages[0].get("role") == "system":
        return messages[0]["content"]

    return fallback_prompt


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
        assets_dir = _get_assets_dir(state)
        file_tools = FileTools(workspace, skill_dir=skill_dir, assets_dir=assets_dir)

        script_dirs: list[str] = []
        if skill_dir:
            script_dirs.append(skill_dir)
        if assets_dir:
            script_dirs.append(assets_dir)
        terminal_tools = _create_terminal_tools_for_mode(
            workspace, readonly=True, allowed_script_dirs=script_dirs
        )

        file_lc_tools = create_file_tools(file_tools)
        lc_tools: list[BaseTool] = list(file_lc_tools)
        if terminal_tools is not None:
            from app.tools.langchain_tools import RunCommandTool

            cmd_tool = RunCommandTool(terminal_tools=terminal_tools, readonly=True)
            cmd_tool.description = "在项目工作区执行预授权终端命令。plan 模式下仅限只读命令（ls、cat、git status、python 脚本等）。"
            lc_tools.append(cmd_tool)

        from app.tools.langchain_tools import ReadAssetTool

        lc_tools.append(ReadAssetTool(file_tools=file_tools))

        lc_tools.extend(_make_loop_tools(state, self._services.event_bus))

        tool_handlers = _build_tool_handlers(file_tools, terminal_tools)
        tool_handlers.pop("write_file", None)

        # 构建回退用的硬编码提示词
        fallback_prompt = PLAN_MODE_SYSTEM_PROMPT.format(
            tool_list=_format_tool_list(lc_tools),
            user_prompt=self._context.prompt,
            plan_spec=PLAN_SPEC,
        )
        caps_text = ""
        if state.selected_capabilities and getattr(state.selected_capabilities, "skill", None):
            skill = state.selected_capabilities.skill
            skill_dir_str = str(skill.source_path.parent)
            caps_text = f"\n\n## 已选择的 Skill\n\n**{skill.name}** (ID: {skill.id}): {skill.description}\n\nSkill 目录: `{skill_dir_str}`\n\n你可以用 `read_asset(relative_path='skills/{skill.id}/SKILL.md')` 读取详细规则，或用 `run_command` 执行 `{skill_dir_str}/scripts/search.py` 等脚本。"
        else:
            index = getattr(state, "_asset_index", None)
            if index is not None:
                skills = index.skill_registry.all()
                if skills:
                    caps_text = "\n\n## 可用 Skill 列表\n\n你可以使用 `select_skill(skill_id, reason)` 选择一个适合当前任务的 Skill。\n\n"
                    for s in skills:
                        caps_text += f"- **{s.id}**: {s.description}\n"
        fallback_prompt += caps_text

        # 使用 PromptComposer 或回退
        system_prompt = _compose_system_prompt(
            state, self._context, self._services, lc_tools, fallback_prompt
        )

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
        assets_dir = _get_assets_dir(state)
        file_tools = FileTools(workspace, skill_dir=skill_dir, assets_dir=assets_dir)

        terminal_tools = _create_terminal_tools_for_mode(workspace, readonly=False)

        from app.tools.langchain_tools import create_all_tools

        lc_tools: list[BaseTool] = create_all_tools(file_tools, terminal_tools=terminal_tools)
        from app.tools.langchain_tools import ReadAssetTool

        lc_tools.append(ReadAssetTool(file_tools=file_tools))
        lc_tools.extend(_make_loop_tools(state, self._services.event_bus))

        tool_handlers = _build_tool_handlers(file_tools, terminal_tools)

        # 构建回退用的硬编码提示词
        outline_text = "暂无实现规划"
        if state.implementation_outline:
            if isinstance(state.implementation_outline, dict):
                outline_text = state.implementation_outline.get("text", str(state.implementation_outline))
            else:
                outline_text = str(state.implementation_outline)

        fallback_prompt = IMPLEMENT_MODE_SYSTEM_PROMPT.format(
            tool_list=_format_tool_list(lc_tools),
            user_prompt=self._context.prompt,
            implementation_outline=outline_text,
        )
        if state.selected_capabilities and getattr(state.selected_capabilities, "skill", None):
            skill = state.selected_capabilities.skill
            skill_dir_str = str(skill.source_path.parent)
            skill_text = f"\n\n## 已选择的 Skill\n\n**{skill.name}** (ID: {skill.id}): {skill.description}\n\nSkill 目录: `{skill_dir_str}`\n\n你可以用 `read_asset(relative_path='skills/{skill.id}/SKILL.md')` 读取详细规则，或用 `run_command` 执行 `{skill_dir_str}/scripts/search.py` 等脚本。"
            fallback_prompt += skill_text

        # 使用 PromptComposer 或回退
        system_prompt = _compose_system_prompt(
            state, self._context, self._services, lc_tools, fallback_prompt
        )

        logger.info("implement_step | iteration=%d mode=%s", state.iteration + 1, state.mode)

        result = await _execute_single_step(
            state,
            self._context,
            self._services,
            system_prompt,
            lc_tools,
            tool_handlers,
            file_tools,
        )

        # implement 完成后标记，供 route_step 判断
        if result.status == "running":
            result.implement_just_finished = True
            result.validate_just_finished = False

        return result
