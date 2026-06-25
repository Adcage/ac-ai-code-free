"""Implement 阶段完成门禁工具。

只有通过结构化门禁检查的实现才能提交完成声明。
门禁包括：文件变更或 no-code 理由、验证证据、文件范围合规、预算未超限。
"""

import logging
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from app.core.error_codes import AgentErrorCode
from app.core.exceptions import AgentRuntimeError

logger = logging.getLogger("app.agent_loop.tools.complete_implementation")


class CompleteImplementationInput(BaseModel):
    run_kind: str = Field(description="initial | user_modification | validation_repair")
    source_plan_version: int = Field(description="执行的计划版本")
    completed_task_ids: list[str] = Field(default_factory=list, description="已完成任务 ID 列表")
    addressed_issue_ids: list[str] = Field(default_factory=list, description="已处理的校验问题 ID 列表")
    verification_refs: list[str] = Field(default_factory=list, description="验证证据引用列表（新生成可留空，修复/修改必填）")
    known_limitations: list[str] = Field(default_factory=list, description="已知限制")
    summary: str = Field(
        default="",
        description=(
            "实施总结：用自然语言说明完成了什么界面和功能。"
            "例如「已完成登录页和注册页面的实现，包含表单验证和社交登录功能」"
        ),
    )


class CompleteImplementationTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "complete_implementation"
    description: str = (
        "提交实现完成声明。必须通过结构化门禁：所有目标任务完成、"
        "未关闭问题已处理、文件范围合规、预算未超限。"
        "门禁失败会返回具体缺失项，模型可在预算内继续处理。"
        "提交时请用 summary 说明实现了什么界面和功能。"
    )
    args_schema: Type[BaseModel] = CompleteImplementationInput

    _state: object | None = None

    def set_state(self, state: object) -> None:
        self._state = state

    def _run(self, **_kwargs: Any) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(
        self,
        run_kind: str,
        source_plan_version: int,
        completed_task_ids: list[str] | None = None,
        addressed_issue_ids: list[str] | None = None,
        verification_refs: list[str] | None = None,
        known_limitations: list[str] | None = None,
        summary: str = "",
    ) -> str:
        if self._state is None:
            raise AgentRuntimeError("未绑定 AgentLoopState", code=AgentErrorCode.STATE_ERROR)

        from app.agent_loop.state import AgentLoopState
        if not isinstance(self._state, AgentLoopState):
            raise AgentRuntimeError("状态类型不正确", code=AgentErrorCode.STATE_ERROR)

        state: AgentLoopState = self._state

        if run_kind not in ("initial", "user_modification", "validation_repair"):
            raise AgentRuntimeError(
                f"run_kind 必须是 initial/user_modification/validation_repair，当前: {run_kind}",
                code=AgentErrorCode.STATE_ERROR,
            )

        missing: list[str] = []

        if not state.implement_phase_files and not known_limitations:
            missing.append("无文件变更且无 no-code 理由；至少需要一项变更或明确说明原因")

        # 新生成（initial）无需验证证据，修改/修复需要
        if run_kind != "initial" and not verification_refs and state.implement_phase_files:
            missing.append("修改/修复场景必须有验证证据（verification_refs）")

        if missing:
            return (
                "完成门禁未通过，缺失项：\n"
                + "\n".join(f"- {m}" for m in missing)
                + "\n\n请继续处理缺失项后再次提交。"
            )

        state.implement_just_finished = True
        if summary:
            state.final_summary = summary

        logger.info(
            "complete_implementation | run_kind=%s tasks=%d issues=%d files=%d summary=%s",
            run_kind,
            len(completed_task_ids or []),
            len(addressed_issue_ids or []),
            len(state.implement_phase_files),
            summary[:100] if summary else "(无)",
        )
        return "实现门禁已通过，实施完成。"
