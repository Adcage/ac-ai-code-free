from typing import Literal

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field


class DecideValidationInput(BaseModel):
    verdict: Literal["pass", "fail"] = Field(description="校验结论")
    issues: list[str] = Field(default=[], description="发现的问题列表（fail 时必填）")
    suggestions: list[str] = Field(default=[], description="修复建议")


class DecideValidationTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "decide_validation"
    description: str = "校验完成后调用此工具输出结论。必须调用。"
    args_schema: type[BaseModel] = DecideValidationInput

    _state: object | None = None

    def set_state(self, state) -> None:
        self._state = state

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(
        self,
        verdict: str = "pass",
        issues: list[str] | None = None,
        suggestions: list[str] | None = None,
    ) -> str:
        if self._state is not None:
            state = self._state
            if verdict == "pass":
                state.validation_status = "passed"
                state.validation_failures = []
            else:
                state.validation_status = "failed"
                state.validation_failures = [
                    {"issue": issue, "suggestion": suggestion}
                    for issue, suggestion in zip(issues or [], suggestions or [])
                ]
                # 如果 issues 比 suggestions 多，补充空 suggestion
                remaining_issues = (issues or [])[(len(suggestions or [])):]
                for issue in remaining_issues:
                    state.validation_failures.append({"issue": issue, "suggestion": ""})

                # 追加修复反馈到对话消息
                feedback = "## 校验反馈\n\n上次生成的代码存在以下问题：\n"
                for i, issue in enumerate(issues or [], 1):
                    feedback += f"{i}. {issue}\n"
                matching_suggestions = suggestions or []
                if matching_suggestions:
                    feedback += "\n修复建议：\n"
                    for i, s in enumerate(matching_suggestions, 1):
                        feedback += f"{i}. {s}\n"
                state.conversation_messages.append({"role": "system", "content": feedback})

            state.validate_just_finished = True
            state.implement_just_finished = False
            # validate_iterations 由 ValidateStepNode 每步统一递增，此处不再重复计数

        issues_count = len(issues or [])
        return f"校验结论：{verdict}" + (f"，发现 {issues_count} 个问题" if verdict == "fail" else "")
