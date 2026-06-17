from dataclasses import dataclass, field
from typing import Any, Literal

from app.runtime.state import ToolCallRecord


@dataclass
class AgentLoopState:
    mode: Literal["plan", "implement"] = "plan"
    status: Literal["running", "completed", "failed"] = "running"

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
