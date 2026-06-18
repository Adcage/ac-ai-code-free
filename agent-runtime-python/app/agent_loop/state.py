import json
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from app.runtime.state import ToolCallRecord

logger = logging.getLogger("app.agent_loop.state")

_PERSIST_FIELDS = (
    "mode", "status", "iteration", "mode_switches",
    "selected_skill_id", "implementation_outline", "clarification_questions",
    "files_touched", "executed_tool_calls", "conversation_messages",
    "resolved_model", "plan_iterations",
    # 前置路由
    "route_decided", "route_decision", "route_iterations",
    "recommended_code_gen_type",
    # 校验循环
    "validate_iterations", "validation_failures", "validation_check_results",
    "validation_status", "implement_just_finished", "validate_just_finished",
    # 测试模式
    "is_test",
    # 提示词追踪
    "prompt_modules_applied",
)


@dataclass
class AgentLoopState:
    mode: Literal["plan", "implement", "validate"] = "plan"
    status: Literal["running", "completed", "failed", "waiting_for_user"] = "running"

    iteration: int = 0
    max_iterations: int = 50
    mode_switches: int = 0
    max_mode_switches: int = 6

    selected_capabilities: Any | None = None
    implementation_outline: dict | None = None
    clarification_questions: list[dict] = field(default_factory=list)

    files_touched: list[str] = field(default_factory=list)
    executed_tool_calls: list[ToolCallRecord] = field(default_factory=list)
    model_response_text: str = ""

    resolved_model: dict[str, Any] | None = None

    conversation_messages: list[dict] = field(default_factory=list)
    skill_context: dict | None = None

    _asset_index: Any = None
    selected_skill_id: str | None = None
    plan_iterations: int = 0
    max_plan_iterations: int = 15

    # 前置路由
    route_decided: bool = False
    route_decision: dict | None = None   # {"mode": "plan", "code_gen_type": "", "reason": ""}
    route_iterations: int = 0
    max_route_iterations: int = 3
    recommended_code_gen_type: str | None = None

    # 校验循环
    validate_iterations: int = 0
    max_validate_iterations: int = 3
    validation_failures: list[dict] = field(default_factory=list)
    validation_check_results: list[dict] | None = None
    validation_status: Literal["pending", "passed", "failed"] = "pending"

    # 阶段标记（用于 route_step 提示词模块判断）
    implement_just_finished: bool = False
    validate_just_finished: bool = False

    # 测试模式
    is_test: bool = False

    # 提示词追踪
    prompt_modules_applied: list[str] = field(default_factory=list)

    def serialize(self) -> str:
        data = {}
        for f in _PERSIST_FIELDS:
            val = getattr(self, f)
            if f == "executed_tool_calls":
                val = [
                    {"id": r.id, "name": r.name, "arguments": r.arguments, "result": r.result}
                    for r in val
                ]
            if f == "resolved_model" and isinstance(val, dict):
                val = {k: v for k, v in val.items() if k != "apiKey"}
            if f == "route_decision" and isinstance(val, dict):
                val = val  # 保留完整路由决策
            data[f] = val
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def deserialize(cls, json_str: str) -> "AgentLoopState":
        data = json.loads(json_str)
        executed = data.pop("executed_tool_calls", [])
        data["executed_tool_calls"] = [
            ToolCallRecord(
                id=r["id"], name=r["name"],
                arguments=r["arguments"], result=r.get("result"),
            )
            for r in executed
        ]
        state = cls()
        for key, val in data.items():
            if hasattr(state, key):
                setattr(state, key, val)
        return state
