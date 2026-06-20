import logging
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("app.agent_loop.tools.switch_mode")


class SwitchModeInput(BaseModel):
    mode: str = Field(description="目标模式: implement 或 plan")
    reason: str = Field(default="", description="切换原因")


class SwitchModeTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "switch_mode"
    description: str = (
        "进入代码实现阶段。调用后你将获得 write_file 权限，可以创建和编辑项目文件。"
        "在理解用户需求并制定实现计划后调用。也可以返回 plan 模式重新规划。"
    )
    args_schema: Type[BaseModel] = SwitchModeInput

    _state: object | None = None

    def set_state(self, state: object) -> None:
        self._state = state

    def _run(self, mode: str, reason: str = "") -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, mode: str, reason: str = "") -> str:
        if self._state is None:
            return "错误：未绑定 AgentLoopState"

        state = self._state

        if mode == "implement":
            if state.mode != "plan":
                return f"当前不在 plan 模式，无法切换到 implement（当前模式: {state.mode}）"
            if not state.implementation_outline:
                return "请先调用 write_plan 写入实现计划，然后才能切换到 implement 模式"
            logger.info("switch_mode | plan -> implement | reason=%s", reason)
            state.mode = "implement"
            state.mode_switches += 1
            return "已切换到 implement 模式，开始按规划生成代码"

        elif mode == "plan":
            if state.mode != "implement":
                return f"当前不在 implement 模式，无法切换到 plan（当前模式: {state.mode}）"
            if not reason:
                return "请提供切换回 plan 模式的原因"
            logger.info("switch_mode | implement -> plan | reason=%s", reason)
            state.mode = "plan"
            state.mode_switches += 1
            return f"已切换回 plan 模式：{reason}"

        else:
            return f"不支持的模式: {mode}，只支持 plan 或 implement"
