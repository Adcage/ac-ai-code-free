from typing import Literal

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field


class DecideRouteInput(BaseModel):
    mode: Literal["plan", "implement", "validate", "finish"] = Field(
        description="路由目标模式：plan(需规划)、implement(直接实现)、validate(需校验)、finish(直接完成)"
    )
    code_gen_type: str = Field(
        default="",
        description="推荐的应用类型，仅在首次路由且 code_gen_type 未确定时填写：single_file / multi-file / vue_project",
    )
    reason: str = Field(
        default="",
        description="路由理由简述",
    )


class DecideRouteTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "decide_route"
    description: str = "判断请求应进入哪种模式后调用此工具输出决策。必须调用。"
    args_schema: type[BaseModel] = DecideRouteInput

    _state: object | None = None

    def set_state(self, state) -> None:
        self._state = state

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(
        self,
        mode: str = "plan",
        code_gen_type: str = "",
        reason: str = "",
    ) -> str:
        if self._state is not None:
            state = self._state
            state.route_decided = True
            state.route_decision = {
                "mode": mode,
                "code_gen_type": code_gen_type,
                "reason": reason,
            }
            state.mode = mode
            if code_gen_type:
                state.recommended_code_gen_type = code_gen_type
        type_info = f" 应用类型：{code_gen_type}" if code_gen_type else ""
        return f"路由决策已记录：进入 {mode} 模式。{type_info}"
