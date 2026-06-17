import logging
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("app.agent_loop.tools.finish")


class FinishInput(BaseModel):
    summary: str = Field(description="任务完成摘要，说明完成了什么")


class FinishTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "finish"
    description: str = "标记任务完成。完成所有文件生成后调用此工具结束 Agent 循环。"
    args_schema: Type[BaseModel] = FinishInput

    _state: object | None = None

    def set_state(self, state: object) -> None:
        self._state = state

    def _run(self, summary: str) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, summary: str) -> str:
        if self._state is not None:
            self._state.status = "completed"
            if hasattr(self._state, "final_summary"):
                self._state.final_summary = summary

        logger.info("finish | summary=%s", summary)
        return f"任务已完成：{summary}"
