import logging
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("app.agent_loop.tools.finish_tool")


class FinishInput(BaseModel):
    summary: str = Field(description="任务完成摘要，说明完成了什么")


class FinishTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "finish"
    description: str = "标记当前模式的工作完成。完成所有文件生成后调用此工具。"
    args_schema: Type[BaseModel] = FinishInput

    _state: object | None = None

    def set_state(self, state: object) -> None:
        self._state = state

    def _run(self, summary: str) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, summary: str) -> str:
        if self._state is not None:
            state = self._state
            mode = getattr(state, "mode", "plan")

            if mode == "implement":
                # implement 模式下，finish 表示代码生成完成，但需要走 route_step 决定是否校验
                state.status = "running"
                state.implement_just_finished = True
                state.validate_just_finished = False
                logger.info("finish | implement completed, routing to route_step | summary=%s", summary)
                return f"代码生成完成：{summary}\n系统将判断是否需要校验。"
            else:
                # plan / validate 等模式下直接完成
                state.status = "completed"
                if hasattr(state, "final_summary"):
                    state.final_summary = summary
                logger.info("finish | summary=%s", summary)
                return f"任务已完成：{summary}"

        return "任务已完成"
