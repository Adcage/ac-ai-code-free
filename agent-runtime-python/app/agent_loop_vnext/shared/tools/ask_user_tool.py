"""vNext AskUser 工具 — 向用户发起结构化提问，暂停执行等待用户回答。

核心流程：
1. 归一化 inputType → single_select / multi_select
2. 校验：拒绝 text 类型、空 options、空 questions
3. 生成 questionSetId
4. 设置 state.status = "waiting_for_user"
5. 发射 CLARIFICATION_REQUIRED 事件
6. 返回提示文本
"""

import logging
import uuid
from typing import Any, Type

from pydantic import BaseModel, ConfigDict, Field

from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.agent_loop_vnext.state import SingleImplementState

logger = logging.getLogger("app.agent_loop_vnext.shared.tools.ask_user_tool")

PROTOCOL_VERSION = 1


class AskUserInput(BaseModel):
    questions: list[dict] = Field(
        default_factory=list,
        description=(
            "结构化问题列表：每项 {id, prompt, inputType, required, options}。"
            "inputType 仅支持 single_select 和 multi_select。"
        ),
    )


class AskUserTool(AgentTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "AskUser"
    description: str = (
        "向用户发起结构化提问，暂停执行等待用户回答。"
        "每个问题必须提供 prompt/inputType/options，"
        "inputType 仅支持 single_select 和 multi_select。"
    )
    args_schema: Type[BaseModel] = AskUserInput

    state: SingleImplementState | None = None
    event_bus: Any | None = None

    async def _arun(self, questions: list[dict] | None = None) -> str:
        if not questions:
            return "错误：questions 不能为空；至少要包含一个结构化问题"

        if self.state is None:
            return "错误：未绑定 SingleImplementState"

        # 1. 归一化 inputType
        for q in questions:
            raw_input_type = q.get("inputType", "single_select")
            options = q.get("options") or []
            if not isinstance(raw_input_type, str):
                raw_input_type = ""
            val = raw_input_type.strip().lower()

            # 拒绝 text
            if val == "text":
                return (
                    f"错误：inputType={raw_input_type!r} 不被支持；"
                    "AskUser 统一为选择式，只接受 single_select / multi_select，"
                    "自由文本通过前端的\"自定义回答\"实现。"
                )

            # 归一化
            if "multi" in val:
                input_type = "multi_select"
            else:
                input_type = "single_select"
            q["inputType"] = input_type

            # 校验 options
            if not options:
                return (
                    f"错误：inputType={raw_input_type!r} 归一化为 {input_type!r}，"
                    "但未提供 options 选项列表；请重新调用并提供至少 2 个具体选项。"
                )

        # 2. 生成 questionSetId
        question_set_id = f"qs_{uuid.uuid4().hex[:10]}"

        # 3. 归一化问题结构
        normalized_questions: list[dict] = []
        for index, q in enumerate(questions, start=1):
            qid = q.get("id") or f"q{index}"
            input_type = q.get("inputType", "single_select")
            options = q.get("options") or []
            prompt_text = q.get("prompt", "") or q.get("question", "")
            normalized_questions.append({
                "id": qid,
                "prompt": prompt_text,
                "question": prompt_text,
                "inputType": input_type,
                "required": bool(q.get("required", True)),
                "options": [_normalize_option(opt) for opt in options],
            })

        # 4. 设置状态
        self.state.status = "waiting_for_user"
        self.state.pending_question = {
            "questionSetId": question_set_id,
            "protocolVersion": PROTOCOL_VERSION,
            "questions": normalized_questions,
        }

        # 5. 发射 CLARIFICATION_REQUIRED 事件
        if self.event_bus is not None:
            from app.runtime.events import RuntimeEvent, RuntimeEventType

            await self.event_bus.emit(
                RuntimeEvent(
                    RuntimeEventType.CLARIFICATION_REQUIRED,
                    {
                        "questionSetId": question_set_id,
                        "protocolVersion": PROTOCOL_VERSION,
                        "questions": normalized_questions,
                    },
                )
            )

        logger.info(
            "AskUser | questionSetId=%s questions=%d",
            question_set_id,
            len(normalized_questions),
        )
        return f"已向用户提问 questionSetId={question_set_id}（{len(normalized_questions)} 个问题），请等待用户回答。"


def _normalize_option(opt: Any) -> dict[str, Any]:
    """归一化选项为统一结构 {id, label, description, recommended}。"""
    if isinstance(opt, str):
        return {"id": opt, "label": opt, "description": "", "recommended": False}
    if isinstance(opt, dict):
        return {
            "id": str(opt.get("id") or opt.get("value") or opt.get("label", "")),
            "label": str(opt.get("label") or opt.get("id") or opt.get("value", "")),
            "description": str(opt.get("description", "")),
            "recommended": bool(opt.get("recommended", False)),
        }
    return {"id": str(opt), "label": str(opt), "description": "", "recommended": False}
