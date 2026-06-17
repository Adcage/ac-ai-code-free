import logging
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("app.agent_loop.tools.write_plan")


class WritePlanInput(BaseModel):
    outline: str = Field(
        description="实现计划，需包含文件清单（路径、职责、依赖）、生成顺序、技术选型和关键逻辑"
    )


class WritePlanTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "write_plan"
    description: str = (
        "将实现计划写入状态。必须先调用此工具写入计划，才能切换到 implement 模式。"
        "可多次调用更新计划。"
    )
    args_schema: Type[BaseModel] = WritePlanInput

    _state: object | None = None

    def set_state(self, state: object) -> None:
        self._state = state

    def _run(self, outline: str) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, outline: str) -> str:
        if self._state is None:
            return "错误：未绑定 AgentLoopState"

        state = self._state
        state.implementation_outline = {"text": outline}
        logger.info("write_plan | outline length=%d", len(outline))

        return (
            "实现计划已记录。确认计划完整后，调用 switch_mode(mode='implement') 开始生成代码。"
            "如需更新计划，可再次调用 write_plan。"
        )
