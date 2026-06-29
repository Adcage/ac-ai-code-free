# vNext AskUser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AskUser tool to vNext Agent Loop, enabling AI to ask structured questions and pause execution until the user answers.

**Architecture:** AskUserTool sets `state.status = "waiting_for_user"` and emits a `CLARIFICATION_REQUIRED` event. The runner loop detects this status and breaks. The gRPC stream closes with `DONE: waiting_for_user`. When the user answers, a fresh runner is created (no state restore needed); answers travel via `<<RESUME_ANSWERS>>` markers in chat history, rendered to LLM-readable text by `resume_answers.py`.

**Tech Stack:** Python 3.11+, LangChain BaseTool, Pydantic BaseModel, asyncio

## Global Constraints

- vNext must be fully self-contained — NO imports from `app.agent_loop/` (legacy engine)
- Tool name must be `AskUser` (PascalCase, matching vNext convention: Read/Write/Edit/Bash/LoadSkill)
- `inputType` only accepts `single_select` / `multi_select`; `text` must be rejected
- All questions must have non-empty `options` list
- `chat_history.extra.toolCalls` must capture AskUser TOOL_REQUEST (for historical PlanningForm rendering)
- AskUser TOOL_RESULT must be hidden from gRPC stream (no need to persist "已向用户提问")
- `agent_run.loopStateJson` stores only `{"status":"waiting_for_user"}` (minimal trigger for Java `pauseAgentRun`)

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `agent_loop_vnext/shared/tools/ask_user_tool.py` | AskUserTool definition + input normalization |
| Create | `agent_loop_vnext/shared/resume_answers.py` | Resume answer rendering (vNext-owned, no legacy dependency) |
| Create | `tests/agent_loop_vnext/test_ask_user_tool.py` | AskUserTool unit tests |
| Create | `tests/agent_loop_vnext/test_resume_answers.py` | Resume answers unit tests |
| Modify | `agent_loop_vnext/state.py` | Add `pending_question` field |
| Modify | `agent_loop_vnext/runner.py` | Add waiting_for_user break + DONE distinction |
| Modify | `agent_loop_vnext/agents/implementor/tools.py` | Register AskUserTool |
| Modify | `agent_loop_vnext/agents/implementor/prompt.py` | Add AskUser usage hint |
| Modify | `agent_loop_vnext/shared/history.py` | Resume answer rendering in _message_from_role |
| Modify | `agent_loop_vnext/event_mapper.py` | AskUser TOOL_CALL visible, TOOL_RESULT hidden |
| Modify | `agent_loop_vnext/status_strategies.py` | Add AskUserStrategy |
| Modify | `runtime/orchestrator.py` | Pause vs complete based on runner.state.status |

---

### Task 1: resume_answers.py (vNext-owned)

**Files:**
- Create: `agent-runtime-python/app/agent_loop_vnext/shared/resume_answers.py`
- Create: `agent-runtime-python/tests/agent_loop_vnext/test_resume_answers.py`

**Interfaces:**
- Produces: `render_resume_answer_text(prompt: str) -> str`, `parse_resume_answer_payload(prompt: str) -> dict | None`

- [ ] **Step 1: Write failing test for render_resume_answer_text**

```python
# tests/agent_loop_vnext/test_resume_answers.py
import pytest
from app.agent_loop_vnext.shared.resume_answers import (
    RESUME_MARKER,
    parse_resume_answer_payload,
    render_resume_answer_text,
)


class TestRenderResumeAnswerText:
    def test_renders_single_answer(self):
        prompt = f'{RESUME_MARKER}{{"questionSetId":"qs1","answers":{{"q_device":"desktop"}}}}{RESUME_MARKER}'
        result = render_resume_answer_text(prompt)
        assert "[q_device]: desktop" in result
        assert "请继续生成。" in result

    def test_renders_multiple_answers(self):
        prompt = f'{RESUME_MARKER}{{"questionSetId":"qs2","answers":{{"q_theme":"dark","q_layout":"sidebar"}}}}{RESUME_MARKER}'
        result = render_resume_answer_text(prompt)
        assert "[q_theme]: dark" in result
        assert "[q_layout]: sidebar" in result

    def test_no_marker_returns_original(self):
        prompt = "这是一条普通消息"
        result = render_resume_answer_text(prompt)
        assert result == prompt

    def test_empty_answers_renders_skip(self):
        prompt = f'{RESUME_MARKER}{{"questionSetId":"qs3","answers":{{}}}}{RESUME_MARKER}'
        result = render_resume_answer_text(prompt)
        assert "跳过补充需求" in result

    def test_invalid_json_returns_original(self):
        prompt = f"{RESUME_MARKER}not-valid-json{RESUME_MARKER}"
        result = render_resume_answer_text(prompt)
        assert result == prompt


class TestParseResumeAnswerPayload:
    def test_parses_valid_payload(self):
        prompt = f'{RESUME_MARKER}{{"questionSetId":"qs1","answers":{{"q1":"a1"}}}}{RESUME_MARKER}'
        result = parse_resume_answer_payload(prompt)
        assert result is not None
        assert result["questionSetId"] == "qs1"
        assert result["answers"]["q1"] == "a1"

    def test_no_marker_returns_none(self):
        result = parse_resume_answer_payload("no marker here")
        assert result is None

    def test_invalid_json_returns_none(self):
        prompt = f"{RESUME_MARKER}bad-json{RESUME_MARKER}"
        result = parse_resume_answer_payload(prompt)
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-runtime-python && python -m pytest tests/agent_loop_vnext/test_resume_answers.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write resume_answers.py implementation**

```python
# agent_loop_vnext/shared/resume_answers.py
"""vNext resume 答案渲染 — 将 <<RESUME_ANSWERS>> 编码的答案转为 LLM 可读文本。

vNext 完全自包含，不依赖 legacy 引擎（app.agent_loop.resume_answers）。
"""

import json
import logging
import re

logger = logging.getLogger("app.agent_loop_vnext.resume_answers")

RESUME_MARKER = "<<RESUME_ANSWERS>>"


def render_resume_answer_text(prompt: str) -> str:
    """将 <<RESUME_ANSWERS>>{JSON}<<RESUME_ANSWERS>> 转为 LLM 可读文本。

    输入:  <<RESUME_ANSWERS>>{"questionSetId":"qs1","answers":{"q_device":"desktop"}}<<RESUME_ANSWERS>>
    输出:  需求补充：
           [q_device]: desktop

           请继续生成。
    """
    if RESUME_MARKER not in prompt:
        return prompt

    data = parse_resume_answer_payload(prompt)
    if data is None:
        return prompt

    answers = data.get("answers", {}) if isinstance(data, dict) else {}
    if not answers or not isinstance(answers, dict):
        return "跳过补充需求，请继续生成。"

    lines = ["需求补充："]
    question_set_id = data.get("questionSetId") or data.get("question_set_id")
    if question_set_id:
        lines.append(f"[questionSetId]: {question_set_id}")
    for key, value in answers.items():
        lines.append(f"[{key}]: {value}")
    lines.append("")
    lines.append("请继续生成。")

    return "\n".join(lines)


def parse_resume_answer_payload(prompt: str) -> dict | None:
    """从 prompt 中提取 resume 答案 JSON payload。不含标记或格式错误时返回 None。"""
    if RESUME_MARKER not in prompt:
        return None

    pattern = re.escape(RESUME_MARKER) + r"(.*?)" + re.escape(RESUME_MARKER)
    match = re.search(pattern, prompt, re.DOTALL)
    if not match:
        return None

    json_str = match.group(1).strip()
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning("resume 答案 JSON 解析失败, error=%s", e)
        return None

    if not isinstance(data, dict):
        logger.warning("resume 答案数据格式异常, data=%s", data)
        return None
    return data


__all__ = [
    "RESUME_MARKER",
    "parse_resume_answer_payload",
    "render_resume_answer_text",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd agent-runtime-python && python -m pytest tests/agent_loop_vnext/test_resume_answers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd agent-runtime-python
git add app/agent_loop_vnext/shared/resume_answers.py tests/agent_loop_vnext/test_resume_answers.py
git commit -m "feat(vnext): add resume_answers module for AskUser answer rendering"
```

---

### Task 2: AskUserTool

**Files:**
- Create: `agent-runtime-python/app/agent_loop_vnext/shared/tools/ask_user_tool.py`
- Create: `agent-runtime-python/tests/agent_loop_vnext/test_ask_user_tool.py`
- Modify: `agent-runtime-python/app/agent_loop_vnext/state.py` — add `pending_question` field

**Interfaces:**
- Consumes: `AgentTool` base class from `shared/tools/base.py`, `SingleImplementState` from `state.py`
- Produces: `AskUserTool` class with `name="AskUser"`, `args_schema=AskUserInput`

- [ ] **Step 1: Write failing test for AskUserTool**

```python
# tests/agent_loop_vnext/test_ask_user_tool.py
import asyncio
import pytest

from app.agent_loop_vnext.shared.tools.ask_user_tool import AskUserTool, AskUserInput
from app.agent_loop_vnext.state import SingleImplementState
from app.runtime.events import RuntimeEvent, RuntimeEventType


class _StubEventBus:
    """记录发射的事件，用于断言。"""
    def __init__(self):
        self.events: list[RuntimeEvent] = []

    async def emit(self, event: RuntimeEvent):
        self.events.append(event)


class TestAskUserInputTypeNormalization:
    """inputType 归一化测试。"""

    @pytest.mark.asyncio
    async def test_single_choice_normalized_to_single_select(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_choice",
             "options": [{"id": "dark", "label": "深色"}, {"id": "light", "label": "浅色"}]}
        ])
        assert "已向用户提问" in result
        assert state.status == "waiting_for_user"

    @pytest.mark.asyncio
    async def test_multi_normalized_to_multi_select(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "功能？", "inputType": "multi",
             "options": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}]}
        ])
        assert state.status == "waiting_for_user"

    @pytest.mark.asyncio
    async def test_text_type_rejected(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "描述", "inputType": "text", "options": []}
        ])
        assert "错误" in result
        assert "不被支持" in result
        assert state.status == "running"


class TestAskUserValidation:
    """参数校验测试。"""

    @pytest.mark.asyncio
    async def test_empty_questions_rejected(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[])
        assert "错误" in result
        assert state.status == "running"

    @pytest.mark.asyncio
    async def test_no_options_rejected(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "选一个", "inputType": "single_select", "options": []}
        ])
        assert "错误" in result
        assert "options" in result

    @pytest.mark.asyncio
    async def test_no_state_returns_error(self):
        tool = AskUserTool(state=None, event_bus=_StubEventBus())
        result = await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_select",
             "options": [{"id": "dark", "label": "深色"}]}
        ])
        assert "错误" in result


class TestAskUserEventEmission:
    """事件发射和状态设置测试。"""

    @pytest.mark.asyncio
    async def test_emits_clarification_required(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_select",
             "options": [{"id": "dark", "label": "深色"}, {"id": "light", "label": "浅色"}]}
        ])
        assert any(e.event_type == RuntimeEventType.CLARIFICATION_REQUIRED for e in bus.events)
        clarification = next(e for e in bus.events if e.event_type == RuntimeEventType.CLARIFICATION_REQUIRED)
        assert "questionSetId" in clarification.data
        assert len(clarification.data["questions"]) == 1

    @pytest.mark.asyncio
    async def test_sets_waiting_for_user_status(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_select",
             "options": [{"id": "dark", "label": "深色"}]}
        ])
        assert state.status == "waiting_for_user"
        assert state.pending_question is not None
        assert "questionSetId" in state.pending_question

    @pytest.mark.asyncio
    async def test_pending_question_stores_normalized_data(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        await tool._arun(questions=[
            {"id": "q1", "prompt": "配色？", "inputType": "single_choice",
             "options": [{"id": "dark", "label": "深色"}, {"id": "light", "label": "浅色"}]}
        ])
        assert state.pending_question["questions"][0]["inputType"] == "single_select"


class TestAskUserOptionNormalization:
    """选项归一化测试。"""

    @pytest.mark.asyncio
    async def test_string_option_normalized_to_dict(self):
        state = SingleImplementState()
        bus = _StubEventBus()
        tool = AskUserTool(state=state, event_bus=bus)
        await tool._arun(questions=[
            {"id": "q1", "prompt": "选一个", "inputType": "single_select",
             "options": ["dark", "light"]}
        ])
        q = state.pending_question["questions"][0]
        assert q["options"][0] == {"id": "dark", "label": "dark", "description": "", "recommended": False}
        assert q["options"][1] == {"id": "light", "label": "light", "description": "", "recommended": False}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-runtime-python && python -m pytest tests/agent_loop_vnext/test_ask_user_tool.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Add `pending_question` field to SingleImplementState**

In `agent_loop_vnext/state.py`, add `pending_question` field:

```python
@dataclass
class SingleImplementState:
    """vNext 最小状态，只跟踪运行进度。"""

    status: str = "running"  # running | completed | failed | waiting_for_user
    iteration: int = 0
    loaded_skills: dict[str, LoadedSkill] = field(default_factory=dict)
    pending_question: dict | None = None  # ask_user 暂停时保存的问题结构，仅运行时使用
```

- [ ] **Step 4: Write AskUserTool implementation**

```python
# agent_loop_vnext/shared/tools/ask_user_tool.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd agent-runtime-python && python -m pytest tests/agent_loop_vnext/test_ask_user_tool.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd agent-runtime-python
git add app/agent_loop_vnext/shared/tools/ask_user_tool.py app/agent_loop_vnext/state.py tests/agent_loop_vnext/test_ask_user_tool.py
git commit -m "feat(vnext): add AskUserTool with inputType normalization and validation"
```

---

### Task 3: Register AskUserTool + Prompt hint

**Files:**
- Modify: `agent-runtime-python/app/agent_loop_vnext/agents/implementor/tools.py`
- Modify: `agent-runtime-python/app/agent_loop_vnext/agents/implementor/prompt.py`

**Interfaces:**
- Consumes: `AskUserTool` from Task 2

- [ ] **Step 1: Register AskUserTool in create_implementor_tools**

In `tools.py`, add import and registration:

```python
# Add import at top
from app.agent_loop_vnext.shared.tools.ask_user_tool import AskUserTool

# Add to the returned list in create_implementor_tools
def create_implementor_tools(
    file_tools: FileTools,
    skill_registry: SkillRegistry | None = None,
    state: SingleImplementState | None = None,
) -> list[AgentTool]:
    return [
        ReadTool(file_tools=file_tools, state=state),
        WriteTool(file_tools=file_tools),
        EditTool(file_tools=file_tools),
        InsertTool(file_tools=file_tools),
        GlobTool(file_tools=file_tools),
        GrepTool(file_tools=file_tools),
        LoadSkillTool(skill_registry=skill_registry, state=state),
        BashTool(file_tools=file_tools),
        AskUserTool(state=state),  # event_bus injected by runner after creation
    ]
```

Note: `AskUserTool` needs both `state` and `event_bus`. The `state` is injected here. The `event_bus` must be injected by the runner (see Task 4) since it's not available at tool creation time. We'll set it after `create_implementor_tools` returns.

- [ ] **Step 2: Add AskUser hint in prompt**

In `prompt.py`, add a line to `_render_role`:

```python
def _render_role(self) -> str:
    return (
        "你是一个专业的代码实现助手，负责理解用户需求并生成代码实现。\n"
        "\n"
        "工作方式：\n"
        "- 和用户正常对话交流，理解需求\n"
        "- 需要实现代码时，使用工具创建或修改文件\n"
        "- 需要了解项目现有结构时，使用 Read 工具查看\n"
        "- 需要搜索文件时，使用 Glob 按文件名搜索或 Grep 按内容搜索\n"
        "- 需要执行命令时（如安装依赖、构建项目），使用 Bash 工具\n"
        "- 需要向用户提问以明确需求时，使用 AskUser 工具\n"
        "- Bash 工具每次只能执行一条命令，不支持 &&、||、|、; 等操作符。多条命令请分多次调用\n"
        "- 不需要工具时直接回复，不要主动调用工具"
    )
```

- [ ] **Step 3: Commit**

```bash
cd agent-runtime-python
git add app/agent_loop_vnext/agents/implementor/tools.py app/agent_loop_vnext/agents/implementor/prompt.py
git commit -m "feat(vnext): register AskUserTool and add prompt hint"
```

---

### Task 4: Runner pause logic + event_bus injection

**Files:**
- Modify: `agent-runtime-python/app/agent_loop_vnext/runner.py`

**Interfaces:**
- Consumes: `SingleImplementState.status == "waiting_for_user"` from Task 2

- [ ] **Step 1: Add event_bus injection after tool creation**

In `runner.py`, after `tools = create_implementor_tools(...)`, inject `event_bus`:

```python
# After line 53 (tools = create_implementor_tools(...))
# Inject event_bus into AskUserTool
for tool in tools:
    if hasattr(tool, 'event_bus') and tool.event_bus is None:
        tool.event_bus = self._event_bus
```

- [ ] **Step 2: Add waiting_for_user break in loop**

In the `while True` loop, after `self._state.iteration += 1` (around line 103), add:

```python
                # AskUser 触发暂停
                if self._state.status == "waiting_for_user":
                    logger.info("ask_user triggered, pausing loop | iteration=%d", self._state.iteration)
                    break
```

- [ ] **Step 3: Distinguish DONE event by status**

Replace the single DONE emit (lines 106-109) with status-aware version:

```python
            # 发射完成事件
            if self._state.status == "waiting_for_user":
                await self._event_bus.emit(RuntimeEvent(
                    RuntimeEventType.DONE,
                    {"message": "waiting_for_user"},
                ))
            else:
                await self._event_bus.emit(RuntimeEvent(
                    RuntimeEventType.DONE,
                    {"message": "对话完成"},
                ))
```

- [ ] **Step 4: Commit**

```bash
cd agent-runtime-python
git add app/agent_loop_vnext/runner.py
git commit -m "feat(vnext): runner pauses on AskUser waiting_for_user status"
```

---

### Task 5: HistoryBuilder resume answer rendering

**Files:**
- Modify: `agent-runtime-python/app/agent_loop_vnext/shared/history.py`

**Interfaces:**
- Consumes: `render_resume_answer_text` from Task 1

- [ ] **Step 1: Add resume marker handling in _message_from_role**

In `history.py`, modify `_message_from_role` method to detect and render `<<RESUME_ANSWERS>>`:

```python
    async def _message_from_role(
        self,
        role: str,
        content: str,
        attachments: tuple[AttachmentInfo, ...] = (),
    ) -> BaseMessage:
        """将数据库 role 字符串转为 LangChain 消息类型。"""
        normalized = role.strip().lower()
        if normalized in {"assistant", "ai"}:
            return AIMessage(content=content)
        # vNext resume 答案渲染（自包含，不依赖 legacy）
        if "<<RESUME_ANSWERS>>" in content:
            from app.agent_loop_vnext.shared.resume_answers import render_resume_answer_text
            content = render_resume_answer_text(content)
        if attachments:
            return await self._build_user_message(content, attachments)
        return HumanMessage(content=content)
```

- [ ] **Step 2: Commit**

```bash
cd agent-runtime-python
git add app/agent_loop_vnext/shared/history.py
git commit -m "feat(vnext): HistoryBuilder renders <<RESUME_ANSWERS>> markers in user messages"
```

---

### Task 6: Event mapper — AskUser TOOL_CALL visible, TOOL_RESULT hidden

**Files:**
- Modify: `agent-runtime-python/app/agent_loop_vnext/event_mapper.py`
- Modify: `agent-runtime-python/app/agent_loop_vnext/status_strategies.py`

**Interfaces:**
- Consumes: AskUser tool name `"AskUser"` from Task 2

- [ ] **Step 1: Update event_mapper.py constants and logic**

Update `_VISIBLE_TOOLS` and change hidden tools logic:

```python
# Replace _VISIBLE_TOOLS and _HIDDEN_TOOLS with:
_VISIBLE_TOOLS = frozenset({
    "Read",
    "Write",
    "Edit",
    "Insert",
    "Glob",
    "Grep",
    "LoadSkill",
    "Bash",
    "AskUser",
})

# TOOL_RESULT 隐藏列表（这些工具的执行结果不需要发到前端/存库）
_HIDDEN_TOOLS_RESULT = frozenset({"AskUser"})
```

Update `_map_tool_call` — remove the `tool_name in _HIDDEN_TOOLS` check (AskUser TOOL_CALL should now be visible):

The existing `_map_tool_call` checks `if tool_name in _HIDDEN_TOOLS: return []`. Replace `_HIDDEN_TOOLS` usage with a check that only hides TOOL_RESULT:

```python
    def _map_tool_call(
        self, sequenced_event: SequencedRuntimeEvent
    ) -> list[code_generation_pb2.CodeGenerationEvent]:
        data = sequenced_event.event.data
        tool_name = data.get("name", "")

        # No tools are hidden from TOOL_CALL anymore (AskUser needs to be visible for extra.toolCalls)
```

Update `_map_tool_result` — hide AskUser results:

```python
    def _map_tool_result(
        self, sequenced_event: SequencedRuntimeEvent
    ) -> list[code_generation_pb2.CodeGenerationEvent]:
        data = sequenced_event.event.data
        tool_name = data.get("name", "")

        if tool_name in _HIDDEN_TOOLS_RESULT:
            return []
```

- [ ] **Step 2: Add AskUserStrategy to status_strategies.py**

Add the strategy class and register it:

```python
class AskUserStrategy(ToolStatusStrategy):
    """AskUser 提问策略。"""

    def match(self, tool_name: str) -> bool:
        return tool_name == "AskUser"

    def get_description(self, tool_name: str, args: dict[str, Any], is_test: bool = False) -> str:
        return "正在向用户提问"


# Add to _registry list
_registry: list[ToolStatusStrategy] = [
    FileStrategy(),
    SearchStrategy(),
    SkillStrategy(),
    AskUserStrategy(),
    BashStrategy(),
]
```

- [ ] **Step 3: Commit**

```bash
cd agent-runtime-python
git add app/agent_loop_vnext/event_mapper.py app/agent_loop_vnext/status_strategies.py
git commit -m "feat(vnext): AskUser TOOL_CALL visible in gRPC stream, TOOL_RESULT hidden"
```

---

### Task 7: Orchestrator pause vs complete

**Files:**
- Modify: `agent-runtime-python/app/runtime/orchestrator.py`

**Interfaces:**
- Consumes: `runner.state.status` from Task 4

- [ ] **Step 1: Update _run_single_implement_vnext to handle waiting_for_user**

In the `_execute()` function inside `_run_single_implement_vnext`, replace the hard-coded `loop_state_json=""` with status-aware logic. Find the `complete_agent_run` call inside the `try` block (around line 440-447) and update:

```python
            try:
                runner = SingleImplementLoopRunner(context, services)
                await runner.run()

                latency_ms = int((time.monotonic() - start_time) * 1000)
                # 根据 runner 状态决定完成还是暂停
                loop_state_json = ""
                success = runner.state.status == "completed"
                if runner.state.status == "waiting_for_user":
                    # 最小非空 JSON 触发 Java pauseAgentRun 逻辑
                    loop_state_json = '{"status":"waiting_for_user"}'

                await self._platform_client.complete_agent_run(
                    agent_run_id=agent_run_id,
                    success=success,
                    workspace_path=context.workspace_path,
                    latency_ms=latency_ms,
                    error_message="",
                    loop_state_json=loop_state_json,
                )
```

- [ ] **Step 2: Commit**

```bash
cd agent-runtime-python
git add app/runtime/orchestrator.py
git commit -m "feat(vnext): orchestrator pauses agent_run on AskUser waiting_for_user"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** Each section in the design doc maps to a task
  - AskUserTool → Task 2
  - State extension → Task 2
  - Runner pause → Task 4
  - Orchestrator pause → Task 7
  - Event mapper → Task 6
  - HistoryBuilder resume → Task 5
  - Resume answers → Task 1
  - Tool registration + prompt → Task 3
- [x] **Placeholder scan:** No TBD/TODO/fill-in-later. All code blocks are complete.
- [x] **Type consistency:** `AskUserTool` name is `"AskUser"` (PascalCase) consistently across all tasks. `pending_question` field type `dict | None` consistent in state.py and test assertions. `event_bus` injection pattern matches how `state` is injected.
