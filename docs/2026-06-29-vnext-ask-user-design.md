# vNext AskUser 功能设计

> 日期：2026-06-29
> 状态：已确认

## 1. 概述

在 vNext Agent Loop 中添加 AskUser 工具，允许 AI 向用户发起结构化提问，暂停执行等待用户回答后继续。

核心原则：**vNext 完全自包含，不依赖 legacy 引擎任何代码。**

## 2. 设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 暂停模式 | 流中断 + 新请求恢复 | Web 平台无法在服务端阻塞等待，gRPC 流有超时 |
| 状态恢复 | 不需要 loop_state_json | vNext state 极简，新请求从 chat_history 重建即可 |
| 提问数据持久化 | chat_history.extra.toolCalls | AskUser TOOL_REQUEST 事件正常发射，Java 采集到 extra |
| 答案传递 | 保留 <<RESUME_ANSWERS>> 标记 | 前端已有完整编码/解码逻辑 |
| resume 逻辑 | vNext 自有，不引用 legacy | legacy 可能删除，两链路零依赖 |

## 3. 改动清单

### 3.1 新增文件

| 文件 | 内容 |
|------|------|
| `agent_loop_vnext/shared/tools/ask_user_tool.py` | AskUserTool：结构化提问工具 |
| `agent_loop_vnext/shared/resume_answers.py` | Resume 答案渲染工具（vNext 自有） |

### 3.2 修改文件

| 文件 | 改动 | 侵入性 |
|------|------|--------|
| `agent_loop_vnext/state.py` | `status` 新增 `"waiting_for_user"` 取值，加 `pending_question` 字段 | 追加字段 |
| `agent_loop_vnext/runner.py` | 循环末尾加 1 行状态检查 + DONE 事件区分状态 | 追加 2 处 |
| `agent_loop_vnext/agents/implementor/tools.py` | `create_implementor_tools` 中注册 AskUserTool | 追加 1 行 |
| `agent_loop_vnext/agents/implementor/prompt.py` | `_render_role` 中提示 AskUser 工具用途 | 追加说明 |
| `agent_loop_vnext/shared/history.py` | `_message_from_role` 中处理 <<RESUME_ANSWERS>> 标记 | 追加 3 行 |
| `agent_loop_vnext/event_mapper.py` | AskUser TOOL_CALL 正常发射，TOOL_RESULT 隐藏 | 改常量 |
| `agent_loop_vnext/status_strategies.py` | 新增 AskUserStrategy | 追加策略 |
| `runtime/orchestrator.py` | `_run_single_implement_vnext` 中根据 runner 状态决定 complete/pause | 改 1 处 |

### 3.3 不需要改动的

- ❌ Java 后端（loop_state_json、pauseAgentRun、claimLatestPausedRun 全部已就绪）
- ❌ 前端（PlanningForm、useSSEChat.ts、planningResume.ts 全部已就绪）
- ❌ gRPC proto（loop_state_json 字段已存在）
- ❌ SingleImplementState 序列化/反序列化（不需要）

## 4. 详细设计

### 4.1 AskUserTool

```python
# agent_loop_vnext/shared/tools/ask_user_tool.py

class AskUserInput(BaseModel):
    questions: list[dict] = Field(
        description="结构化问题列表：每项 {id, prompt, inputType, required, options}"
    )

class AskUserTool(AgentTool):
    name: str = "AskUser"
    description: str = (
        "向用户发起结构化提问，暂停执行等待用户回答。"
        "每个问题必须提供 prompt/inputType/options，"
        "inputType 仅支持 single_select 和 multi_select。"
    )
    args_schema: Type[BaseModel] = AskUserInput

    # 构造器注入
    state: SingleImplementState | None = None
    event_bus: object | None = None  # RuntimeEventBus

    async def _arun(self, questions: list[dict] | None = None) -> str:
        # 1. 归一化 inputType → single_select / multi_select
        # 2. 拒绝 text 类型 / 空 options
        # 3. 生成 questionSetId（qs_<uuid10>）
        # 4. 设置 state.status = "waiting_for_user"
        # 5. 设置 state.pending_question = { questionSetId, questions }
        # 6. 发射 CLARIFICATION_REQUIRED 事件
        # 7. 返回 "已向用户提问，请等待用户回答"
```

工具名使用 `AskUser`（PascalCase），与 vNext 其他工具命名一致（Read/Write/Edit/Bash/LoadSkill）。

### 4.2 SingleImplementState 扩展

```python
@dataclass
class SingleImplementState:
    status: str = "running"  # running | completed | failed | waiting_for_user
    iteration: int = 0
    loaded_skills: dict[str, LoadedSkill] = field(default_factory=dict)
    pending_question: dict | None = None  # 仅运行时使用，不需要序列化
```

不需要 `serialize()` / `deserialize()` 方法。vNext 不使用 `loop_state_json` 恢复状态。

### 4.3 Runner 暂停逻辑

```python
# runner.py run() 方法

# 循环末尾新增状态检查
await self._execute_tool_calls(tool_calls, tools, messages)
self._state.iteration += 1
logger.info("iteration completed | iteration=%d", self._state.iteration)

# 新增：ask_user 触发暂停
if self._state.status == "waiting_for_user":
    logger.info("ask_user triggered, pausing loop | iteration=%d", self._state.iteration)
    break

# DONE 事件区分状态
if self._state.status == "waiting_for_user":
    await self._event_bus.emit(RuntimeEvent(RuntimeEventType.DONE, {"message": "waiting_for_user"}))
else:
    await self._event_bus.emit(RuntimeEvent(RuntimeEventType.DONE, {"message": "对话完成"}))
```

### 4.4 Orchestrator 衔接

```python
# orchestrator.py _run_single_implement_vnext()

# runner 执行完成后
loop_state_json = ""
if runner.state.status == "waiting_for_user":
    # 最小非空 JSON 触发 Java pauseAgentRun 逻辑
    # vNext 不需要恢复状态，但 Java 依赖 loop_state_json 非空来判断暂停
    loop_state_json = '{"status":"waiting_for_user"}'

await self._platform_client.complete_agent_run(
    agent_run_id=agent_run_id,
    success=runner.state.status == "completed",
    workspace_path=context.workspace_path,
    latency_ms=latency_ms,
    error_message="",
    loop_state_json=loop_state_json,
)
```

### 4.5 Event Mapper 改动

```python
# event_mapper.py

# AskUser TOOL_CALL 正常发射（Java 采集到 extra.toolCalls）
_VISIBLE_TOOLS = frozenset({
    "Read", "Write", "Edit", "Insert", "Glob", "Grep",
    "LoadSkill", "Bash", "AskUser",
})

# AskUser TOOL_RESULT 隐藏（"已向用户提问"不需要存库）
_HIDDEN_TOOLS_RESULT = frozenset({"AskUser"})

# _map_tool_call：AskUser 正常处理
# _map_tool_result：AskUser 返回空列表
```

### 4.6 HistoryBuilder Resume 处理

```python
# agent_loop_vnext/shared/history.py

async def _message_from_role(self, role, content, attachments=()):
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

### 4.7 Resume 答案工具（vNext 自有）

```python
# agent_loop_vnext/shared/resume_answers.py

RESUME_MARKER = "<<RESUME_ANSWERS>>"

def render_resume_answer_text(prompt: str) -> str:
    """将 <<RESUME_ANSWERS>>{...}<<RESUME_ANSWERS>> 转为 LLM 可读文本。"""

def parse_resume_answer_payload(prompt: str) -> dict | None:
    """从 prompt 中提取 resume 答案 JSON payload。"""
```

### 4.8 AskUser Status Strategy

```python
# status_strategies.py 新增

class AskUserStrategy(ToolStatusStrategy):
    def match(self, tool_name: str) -> bool:
        return tool_name == "AskUser"

    def get_description(self, tool_name: str, args: dict, is_test: bool = False) -> str:
        return "正在向用户提问"
```

## 5. 完整数据流

### 暂停流程

```
1. 模型调用 AskUserTool
2. AskUserTool._arun():
   - 归一化 inputType
   - 生成 questionSetId
   - state.status = "waiting_for_user"
   - state.pending_question = { questionSetId, questions }
   - 发射 CLARIFICATION_REQUIRED 事件
   - return "已向用户提问，请等待用户回答"
3. ToolMessage 追加到 messages（模型看到工具结果）
4. Runner 循环末尾: state.status == "waiting_for_user" → break
5. 发射 DONE { message: "waiting_for_user" }
6. gRPC 流关闭
7. Orchestrator: loop_state_json = '{"status":"waiting_for_user"}' → Java pauseAgentRun()
8. agent_run.status = "waiting_for_user", SSE 流发送 done 事件

前端侧：
9. useSSEChat 收到 tool_request name=AskUser → 渲染 PlanningForm
10. SSE 流 done → generating = false
```

### 恢复流程

```
1. 用户在 PlanningForm 选择/输入
2. 前端 buildPlanningResumePrompt() 编码答案
3. 前端发新消息（正文含 <<RESUME_ANSWERS>>{...}<<RESUME_ANSWERS>>）
4. Java claimLatestPausedRun() 找到暂停的 agent_run
5. Java 发新 gRPC 请求（新 agent_run_id，loop_state_json=""）
6. Python 创建全新 Runner（不需要恢复状态）
7. HistoryBuilder.build_messages():
   - 遍历 chat_history
   - 用户消息含 <<RESUME_ANSWERS>> → render_resume_answer_text() 转为可读文本
   - 模型看到 "需求补充：[q1]: desktop\n请继续生成。"
8. 模型理解用户选择，继续工作
```

### 历史消息还原

```
1. 前端加载历史消息
2. chat_history.extra.toolCalls 中有 name=AskUser 的 request 记录
3. 前端 parseAskUserStructuredPayload() 解析 arguments
4. 渲染 PlanningForm 只读状态（显示用户已选答案）
```

## 6. 两链路隔离

| | Legacy | vNext |
|---|---|---|
| AskUser 工具 | `agent_loop/tools/ask_user.py` | `agent_loop_vnext/shared/tools/ask_user_tool.py` |
| Resume 工具 | `agent_loop/resume_answers.py` | `agent_loop_vnext/shared/resume_answers.py` |
| HistoryBuilder | `agent_loop/message_builder.py` | `agent_loop_vnext/shared/history.py` |
| 互相引用 | ❌ | ❌ |

legacy 删除时，vNext 不受任何影响。
