# vNext Agent 体系架构设计：Agent 基类提取与多 Agent 协作框架

## 1. 设计目标

**核心目标：** 将当前 `SingleImplementLoopRunner` 中硬编码的「循环引擎」提取为通用 `Agent` 基类，使当前的 Implementor 成为第一个 Agent 子类，并为后续多 Agent 协作（Plan → Implement → Validate）预留扩展点。

**用户明确要求：**

- vNext 是全新链路，**不复用、不参考 legacy 引擎（`agent_loop/`）的任何内容**
- 既支持 Agent **独立工作**（一个请求 → 一个 Agent）
- 也支持 Agent **流水线协作**（一个请求 → 多个 Agent 接力）
- 后续会有多个按职责分工的 Agent（Planner、Implementor、Validator、Reviewer、Architect 等）
- Router Agent 后置——**先把单 Agent 流程跑通**，Router 后面再做
- 当前已实现 AskUser 暂停/恢复，Agent 基类必须统一接管该生命周期

**设计原则：**

- 提取而非重写：当前 Implementor 的所有功能（代码生成、文件操作、AskUser）行为不变
- 物理隔离优于提示词约束：工具权限通过 `bind_tools` 物理隔离，不靠提示词约束
- 扩展点优先：Phase 1 不实现 Pipeline/Router，但接口要为它们留好

## 2. 当前 vNext 现状

### 2.1 代码结构

```
agent_loop_vnext/
├── runner.py          # SingleImplementLoopRunner（循环引擎 + Implementor 角色硬编码在一起）
├── state.py           # SingleImplementState
├── event_mapper.py    # VNextEventMapper
├── status_strategies.py
├── agents/implementor/
│   ├── prompt.py      # ImplementorPromptBuilder
│   └── tools.py       # create_implementor_tools
└── shared/
    ├── tools/
    │   ├── base.py            # AgentTool 基类
    │   ├── file_tools.py      # Read/Write/Edit/Insert/Glob/Grep
    │   ├── bash_tool.py       # Bash
    │   ├── skill_tools.py     # LoadSkill
    │   └── ask_user_tool.py   # AskUser
    ├── history.py             # HistoryBuilder
    ├── resume_answers.py      # <<RESUME_ANSWERS>> 渲染
    └── file_processor.py
```

### 2.2 当前 runner 的 4 个关注点（硬编码在一起）

| 关注点 | 当前形式 | 改造目标 |
|--------|---------|---------|
| 循环引擎 | `_stream_model_call` + `_execute_tool_calls` | Agent 基类复用 |
| 角色定义 | `ImplementorPromptBuilder._render_role()` | 每个 Agent 自定义 |
| 工具集 | `create_implementor_tools()` | 每个 Agent 自选 |
| 生命周期 | runner 处理 AskUser pause/resume | 基类统一处理 |

### 2.3 当前循环引擎核心流程（runner.py:run）

```
1. 创建 Workspace + FileTools
2. create_implementor_tools(file_tools, skill_registry, state)
3. 注入 event_bus 到 AskUserTool
4. model_resolver.load_bundle(context) → resolve(PRIMARY) → chat_model_factory.create()
5. ImplementorPromptBuilder.build_system_prompt()
6. HistoryBuilder.build_messages(context, system_prompt)
7. chat_model.bind_tools(tools)
8. while True:
     a. _stream_model_call() → 流式发射 TEXT_DELTA + 收集 tool_calls
     b. 无 tool_calls → status=completed, break
     c. AIMessage(tool_calls) 追加到 messages
     d. _execute_tool_calls() → 发射 TOOL_CALL/TOOL_RESULT + ToolMessage 追加
     e. iteration++
     f. 检测 status == "waiting_for_user" → break（AskUser 暂停）
9. 发射 DONE（waiting_for_user 或 对话完成）
```

**改造原则：以上 9 步全部移入 Agent 基类，子类只覆盖步骤 5（系统提示词）和步骤 2（工具集）。**

## 3. 架构总览

```
agent_loop_vnext/
├── base/                          ★ 新建：框架核心
│   ├── __init__.py
│   ├── agent.py                   # Agent 基类（通用循环引擎）
│   ├── state.py                   # AgentRunState（通用运行状态）
│   └── result.py                  # AgentResult / PipelineResult
│
├── agents/                        各 Agent 定义
│   ├── __init__.py                # AgentRegistry 注册入口
│   ├── implementor/               ✅ 当前已有，改写为 Agent 子类
│   │   ├── agent.py               #   ImplementorAgent(Agent)
│   │   ├── prompt.py              #   保持不变
│   │   └── tools.py               #   保持不变
│   ├── router/                    ☆ Phase 2 预留
│   ├── reviewer/                  ☆ Phase 4 预留
│   └── architect/                 ☆ Phase 4 预留
│
├── pipeline/                      ☆ Phase 3 预留（Phase 1 只建空目录或不建）
│   ├── executor.py                #   PipelineExecutor
│   └── context_filter.py          #   ContextFilter（分层裁剪）
│
├── shared/                        保持现有不变
│   ├── tools/
│   ├── history.py
│   ├── resume_answers.py
│   └── file_processor.py
│
├── runner.py                      精简为启动器：选 Agent → 执行
├── state.py                       转为引用 base/state.py（保持导入兼容）
├── event_mapper.py                保持不变
└── status_strategies.py           保持不变
```

## 4. Phase 1 核心设计：Agent 基类

### 4.1 Agent 基类

```python
# agent_loop_vnext/base/agent.py
"""Agent 基类：封装「模型调用 → 工具执行 → 循环」的通用引擎。

子类只需定义：
  - name / description：Agent 标识
  - create_tools()：工具集（物理隔离）
  - build_system_prompt()：系统提示词

基类自动处理：模型解析、消息历史构建、循环迭代、工具执行、
AskUser 暂停、错误处理、事件发射。
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app.agent_loop_vnext.base.state import AgentRunState
from app.agent_loop_vnext.base.result import AgentResult
from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.runtime.context import ExecutionContext
from app.runtime.services import RuntimeServices


class Agent(ABC):
    """Agent 基类。"""

    # === 子类必须定义 ===
    name: ClassVar[str]              # "implementor"
    description: ClassVar[str]       # 一句话描述（Router 识别用）

    def __init__(self) -> None:
        self._state: AgentRunState = AgentRunState()
        self._event_bus: Any = None

    @property
    def state(self) -> AgentRunState:
        return self._state

    @abstractmethod
    def create_tools(self, file_tools: Any, services: RuntimeServices) -> list[AgentTool]:
        """子类返回自己的工具集。注入 file_tools 等依赖。"""

    @abstractmethod
    def build_system_prompt(self, context: ExecutionContext, services: RuntimeServices) -> str:
        """子类构建自己的系统提示词。"""

    # === 基类自动处理 ===
    async def run(self, context: ExecutionContext, services: RuntimeServices) -> AgentResult:
        """通用循环引擎。流程见 §2.3。"""
        # 1. Workspace + FileTools
        # 2. create_tools() + 注入 event_bus
        # 3. model_resolver.load_bundle → resolve(PRIMARY) → chat_model_factory.create
        # 4. build_system_prompt()
        # 5. HistoryBuilder.build_messages(context, system_prompt)
        # 6. chat_model.bind_tools(tools)
        # 7. while True: _stream_model_call → tool_calls? → _execute_tool_calls → check waiting_for_user
        # 8. 发射 DONE
        # 9. 返回 AgentResult
```

### 4.2 哪些逻辑进基类，哪些进子类

| 逻辑 | 归属 | 原因 |
|------|------|------|
| 创建 Workspace + FileTools | 基类 | 所有 Agent 都需要 |
| 解析模型配置（model_resolver） | 基类 | 所有 Agent 都需要 |
| 构建消息历史（HistoryBuilder） | 基类 | 所有 Agent 都需要 |
| 流式调用模型 → 发射 TEXT_DELTA | 基类 | 循环引擎核心 |
| 执行工具 → 发射 TOOL_CALL/TOOL_RESULT | 基类 | 循环引擎核心 |
| 检测 AskUser → 暂停 | 基类 | 所有 Agent 都需要 |
| 错误处理 → RUNTIME_ERROR | 基类 | 所有 Agent 都需要 |
| 循环退出条件（无 tool_calls） | 基类 | 通用规则 |
| **工具集定义** | **子类** | 不同 Agent 用不同工具（物理隔离） |
| **系统提示词** | **子类** | 不同 Agent 有不同角色 |
| **可选：前序工作摘要渲染** | **子类** | Pipeline 场景用（Phase 3） |

### 4.3 AgentResult — Agent 执行结果契约

```python
# agent_loop_vnext/base/result.py
from dataclasses import dataclass, field
from typing import Any

from app.agent_loop_vnext.base.state import AgentRunState


@dataclass
class AgentResult:
    """Agent 执行结果。

    - status: completed / failed / waiting_for_user
    - message: Agent 最终回复摘要（纯文本）
    - artifacts: 结构化产出（供下游 Pipeline Agent 消费，Phase 3 用）
    - state: 暂停时保存的完整状态（AskUser resume 用）
    - error: 失败时的错误信息
    """
    status: str
    iteration: int = 0
    message: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)
    state: AgentRunState | None = None
    error: str | None = None


@dataclass
class PipelineResult:
    """Pipeline 执行结果（Phase 3）。"""
    status: str                       # completed / failed / paused
    results: list[AgentResult] = field(default_factory=list)
    failed_at: str | None = None      # 失败的 Agent 名
    paused_at: str | None = None      # 暂停的 Agent 名
```

### 4.4 AgentRunState — 通用状态

当前 `SingleImplementState` 已经通用，迁移为 `AgentRunState`：

```python
# agent_loop_vnext/base/state.py
from dataclasses import dataclass, field, asdict
import json


@dataclass(frozen=True)
class LoadedSkill:
    """已加载的 Skill 摘要。"""
    skill_id: str
    name: str
    description: str
    source_dir: str
    references: tuple[str, ...] = ()


@dataclass
class AgentRunState:
    """通用 Agent 运行状态。"""
    status: str = "running"            # running / completed / failed / waiting_for_user
    iteration: int = 0
    loaded_skills: dict[str, LoadedSkill] = field(default_factory=dict)
    pending_question: dict | None = None   # AskUser 暂停时的问题结构

    def serialize(self) -> str:
        """序列化为 JSON，供 AskUser 暂停时持久化。"""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    @classmethod
    def deserialize(cls, data: str) -> "AgentRunState":
        return cls(**json.loads(data))
```

### 4.5 ImplementorAgent — 当前 Implementor 改写为 Agent 子类

```python
# agent_loop_vnext/agents/implementor/agent.py
from app.agent_loop_vnext.base.agent import Agent
from app.agent_loop_vnext.base.state import AgentRunState
from app.agent_loop_vnext.agents.implementor.prompt import ImplementorPromptBuilder
from app.agent_loop_vnext.agents.implementor.tools import create_implementor_tools
from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.runtime.context import ExecutionContext
from app.runtime.services import RuntimeServices


class ImplementorAgent(Agent):
    """代码实现 Agent —— 当前 vNext 唯一活跃 Agent。"""

    name = "implementor"
    description = "理解用户需求并生成代码实现"

    def create_tools(self, file_tools, services) -> list[AgentTool]:
        skill_registry = None
        if services.asset_manager is not None:
            skill_registry = services.asset_manager.get_index().skill_registry
        return create_implementor_tools(
            file_tools,
            skill_registry=skill_registry,
            state=self._state,
        )

    def build_system_prompt(self, context, services) -> str:
        skill_registry = None
        if services.asset_manager is not None:
            skill_registry = services.asset_manager.get_index().skill_registry
        builder = ImplementorPromptBuilder(context, self._state, skill_registry=skill_registry)
        return builder.build_system_prompt()
```

**关键点：** `prompt.py` 和 `tools.py` 完全不动，只是被 `agent.py` 调用。这保证了当前 Implementor 的行为 100% 不变。

### 4.6 runner.py 精简为启动器

```python
# agent_loop_vnext/runner.py（精简后）
"""vNext Agent 启动器：选择 Agent → 执行 → 返回结果。

Phase 1：写死 implementor。
Phase 2：替换为 RouterAgent 决策。
"""

from app.agent_loop_vnext.agents.implementor.agent import ImplementorAgent
from app.agent_loop_vnext.base.result import AgentResult
from app.runtime.context import ExecutionContext
from app.runtime.services import RuntimeServices


async def run_vnext_agent(context: ExecutionContext, services: RuntimeServices) -> AgentResult:
    """vNext Agent 入口。"""
    # Phase 1：直接使用 implementor
    agent = ImplementorAgent()
    return await agent.run(context, services)
```

### 4.7 orchestrator.py 微调

`RuntimeOrchestrator._run_single_implement_vnext()` 改为调用 `run_vnext_agent()`：

```python
# orchestrator.py 中的关键改动
async def _run_vnext_agent(self, request, run_mode: RunMode):
    from app.agent_loop_vnext.runner import run_vnext_agent
    from app.agent_loop_vnext.base.result import AgentResult

    agent_run_id = int(request.agent_run_id)
    event_bus = EventBus(agent_run_id=agent_run_id)
    services = self._build_services(event_bus)
    start_time = time.monotonic()
    context = await self._build_context(request, run_mode)

    mapper = self._get_mapper()
    if hasattr(mapper, 'set_is_test'):
        mapper.set_is_test(context.is_test)

    async def _execute():
        try:
            result = await run_vnext_agent(context, services)

            latency_ms = int((time.monotonic() - start_time) * 1000)
            loop_state_json = ""
            success = result.status == "completed"
            if result.status == "waiting_for_user":
                loop_state_json = '{"status":"waiting_for_user"}'

            await self._platform_client.complete_agent_run(
                agent_run_id=agent_run_id,
                success=success,
                workspace_path=context.workspace_path,
                latency_ms=latency_ms,
                error_message=result.error or "",
                loop_state_json=loop_state_json,
            )
        except AgentRuntimeError as e:
            # 错误处理保持现有逻辑
            ...
        finally:
            await event_bus.close()

    workflow_task = asyncio.create_task(_execute())
    async for seq_event in self._drain_events(event_bus):
        for proto_event in self._get_mapper().map_event(seq_event):
            yield proto_event
    await workflow_task
```

### 4.8 state.py 兼容性处理

`agent_loop_vnext/state.py` 转为对 `base/state.py` 的引用，保持现有导入兼容：

```python
# agent_loop_vnext/state.py（兼容层）
"""兼容层：保持现有导入路径可用。

新代码应直接从 app.agent_loop_vnext.base.state 导入。
"""
from app.agent_loop_vnext.base.state import AgentRunState as SingleImplementState
from app.agent_loop_vnext.base.state import LoadedSkill

__all__ = ["SingleImplementState", "LoadedSkill"]
```

现有 `tools.py`、`ask_user_tool.py` 等导入 `from app.agent_loop_vnext.state import SingleImplementState` 仍然有效。

## 5. AgentRegistry — Agent 注册与发现（Phase 2 启用）

Phase 1 先不实现完整 Registry，但定义接口。Phase 2 Router 上线时启用：

```python
# agent_loop_vnext/agents/__init__.py（Phase 1 最小实现）
"""Agent 注册中心。

Phase 1：仅手动注册 implementor。
Phase 2：Router 启用后，Router 读取 registry.list_agents() 做路由决策。
"""

class AgentRegistry:
    _agents: dict[str, type["Agent"]] = {}

    @classmethod
    def register(cls, agent_cls: type) -> type:
        cls._agents[agent_cls.name] = agent_cls
        return agent_cls

    @classmethod
    def get(cls, name: str):
        agent_cls = cls._agents.get(name)
        if agent_cls is None:
            raise KeyError(f"未注册的 Agent: {name}")
        return agent_cls()

    @classmethod
    def list_agents(cls) -> list[dict]:
        return [{"name": n, "description": c.description}
                for n, c in cls._agents.items()]

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls._agents
```

注册方式（在 `agents/implementor/__init__.py`）：

```python
from app.agent_loop_vnext.agents import AgentRegistry
from app.agent_loop_vnext.agents.implementor.agent import ImplementorAgent

AgentRegistry.register(ImplementorAgent)
```

## 6. 未来扩展点：多 Agent 协作（Phase 2/3，本节为架构预留）

### 6.1 调研依据：主流框架怎么做

本项目不引入 LangGraph/AutoGen/Swarm 作为运行时框架（保持当前自建循环引擎），但借鉴它们的上下文传递与工具隔离机制：

| 框架 | 上下文传递机制 | 工具隔离机制 |
|------|--------------|------------|
| LangGraph Supervisor | `output_mode=last_message\|full_history` + `add_handoff_messages` 开关 | 每 agent `bind_tools` 物理隔离 |
| AutoGen | Swarm 共享历史 + GraphFlow `MessageFilterConfig` 按源过滤 | 每 agent 构造时传 `tools` |
| OpenAI Swarm | 完整消息历史继承 + `context_variables` 结构化字典累积 | 每 agent `functions` 物理隔离 |
| Anthropic 多智能体原则 | 每个 subagent 独立上下文窗口 + 结构化 handoff | 聚焦任务 + 物理工具集 |

**关键结论：**

1. **没有任何主流框架用「共享全部工具 + 提示词约束」做隔离**。所有框架都通过 `bind_tools` 物理隔离——工具不在列表里，模型看不到，从根源杜绝误调用。提示词约束只作辅助。
2. **「完整历史 vs 摘要」是可配置光谱**，不是二选一。LangGraph `output_mode`、AutoGen `MessageFilter` 都让开发者按场景选。
3. **用户在旧链路的痛点**：上下文含工具调用记录 → 模型幻觉误调用 → 纠错循环 → token 浪费 + 体验差。物理隔离从根源杜绝。

### 6.2 本项目的上下文传递设计：分层裁剪 + 物理隔离

基于调研，本项目采用「**按 Agent 配置的裁剪 + 物理工具隔离**」：

**工具隔离（Phase 1 已留扩展点）：** 每 Agent 通过 `create_tools()` 返回自己的工具集，`bind_tools` 时只绑定这些工具。Validator 不绑定 Write，Implementor 不该有的工具不在列表里。

**上下文裁剪（Phase 3 实现，接口现在预留）：** 每个 Agent 声明「从上游接收什么」：

```
Planner → Implementor:
  保留：所有 HumanMessage（用户需求 + AskUser 回答）
  保留：Planner 最终 AIMessage（设计结论）
  丢弃：Planner 的 ToolMessage（文件读取结果）
  注入：spec.md 路径提示

Implementor → Validator:
  保留：用户原始需求
  保留：Implementor 最终结论
  丢弃：所有工具调用历史
  注入：工作区文件列表（Validator 自己 Read）
```

### 6.3 数据流转三层模型

```
Layer 1: 共享工作区（workspace_path）
  所有 Agent 读写同一工作区。Planner 写 spec.md，Implementor 读 spec.md 并写代码，
  Validator 读代码。无需额外代码，FileTools 本就基于 workspace_path。

Layer 2: AgentResult.artifacts（结构化传递）
  Agent 运行结束产出结构化数据，供下游 Agent 消费。
  Planner → { spec_summary, files_to_create, decisions }
  Implementor → { files_created, summary }
  Validator → { passed, warnings, errors }

Layer 3: 系统提示词注入（语境级传递）
  build_system_prompt() 读取 context.runtime_options["_pipeline_prev_result"]，
  渲染为「前序工作摘要」段落。Agent 可感知自己是独立运行还是在 Pipeline 中。
```

### 6.4 PipelineExecutor（Phase 3）

```python
# agent_loop_vnext/pipeline/executor.py（Phase 3）
class PipelineExecutor:
    async def execute(self, pipeline: list[str], context, services) -> PipelineResult:
        prev_result = None
        results = []
        for agent_name in pipeline:
            agent = AgentRegistry.get(agent_name)
            # 广播 STATUS（前端展示当前阶段）
            await services.event_bus.emit(RuntimeEvent(
                RuntimeEventType.STATUS, {"message": f"{agent.description} 开始工作"}))
            # 上下文增强：注入上游结果
            pipeline_ctx = self._enrich_context(context, prev_result, agent_name)
            result = await agent.run(pipeline_ctx, services)
            if result.status == "failed":
                return PipelineResult(status="failed", failed_at=agent_name, results=results)
            if result.status == "waiting_for_user":
                return PipelineResult(status="paused", paused_at=agent_name, results=results)
            results.append(result)
            prev_result = result
        return PipelineResult(status="completed", results=results)
```

### 6.5 设计决策记录

- **Q: Pipeline 中每个 Agent 用同一模型还是不同模型？**
  A: Phase 1-3 保持现状（共享 PRIMARY 模型）。`Agent.run` 从 `ModelRole.PRIMARY` 解析。未来如需 Plan 用强模型、Validate 用快模型，可在 Pipeline 定义中加 `model_role` 字段，`Agent.run` 接受可选 model_role 参数。**留扩展点，Phase 1 不实现。**

- **Q: Pipeline 中的 AskUser 怎么处理？**
  A: Pipeline 中任何 Agent 触发 AskUser → 整个 Pipeline 暂停为 `paused`，保存状态。用户回答后恢复，从暂停的 Agent 继续。**Phase 3 实现暂停/恢复，Phase 1 不涉及。**

- **Q: Pipeline 是否嵌套？**
  A: 不嵌套。`pipeline: ["planner", "implementor", "validator"]` 是一层列表。保持简单。

- **Q: 是否引入 LangGraph/AutoGen 作为运行时？**
  A: 不引入。当前自建循环引擎（SingleImplementLoopRunner 提取后的 Agent 基类）足够轻量且可控，借鉴框架的机制而非框架本身。

## 7. 文件改动清单（Phase 1）

| 文件 | 操作 | 说明 |
|------|------|------|
| `agent_loop_vnext/base/__init__.py` | 新建 | 导出 Agent / AgentRunState / AgentResult |
| `agent_loop_vnext/base/agent.py` | 新建 | Agent 基类（从 runner.py 提取循环引擎） |
| `agent_loop_vnext/base/state.py` | 新建 | AgentRunState（从 state.py 迁入） |
| `agent_loop_vnext/base/result.py` | 新建 | AgentResult / PipelineResult |
| `agent_loop_vnext/agents/__init__.py` | 新建 | AgentRegistry（Phase 1 最小实现） |
| `agent_loop_vnext/agents/implementor/agent.py` | 新建 | ImplementorAgent(Agent) |
| `agent_loop_vnext/agents/implementor/__init__.py` | 修改 | 注册 ImplementorAgent |
| `agent_loop_vnext/agents/implementor/prompt.py` | 不动 | 被 agent.py 调用 |
| `agent_loop_vnext/agents/implementor/tools.py` | 不动 | 被 agent.py 调用 |
| `agent_loop_vnext/runner.py` | 重构 | 精简为启动器（~30 行） |
| `agent_loop_vnext/state.py` | 重构 | 转为 base/state.py 的兼容引用 |
| `agent_loop_vnext/__init__.py` | 微调 | 导出新接口 |
| `app/runtime/orchestrator.py` | 微调 | `_run_single_implement_vnext` → `_run_vnext_agent` |

**Phase 1 不新建 `pipeline/` 目录**，避免空目录。Phase 3 时再建。

## 8. 验证标准

1. **功能等价**：当前所有功能不变——代码生成（single_file / multi-file / vue_project）、文件操作（Read/Write/Edit/Insert/Glob/Grep）、Bash、LoadSkill、AskUser 暂停/恢复。
2. **新增 Agent 成本**：新增一个 Agent 只需写 `agent.py`（~30 行）+ `prompt.py` + `tools.py`，不碰循环引擎。
3. **测试通过**：所有现有测试通过，包括：
   - `tests/agent_loop_vnext/test_implementor_tools.py`
   - `tests/agent_loop_vnext/test_ask_user_tool.py`
   - `tests/agent_loop_vnext/test_tool_policy.py`
   - `tests/agent_loop_vnext/test_context_engine.py`
   - `tests/integration/test_plan_runtime_progression.py`
   - `tests/integration/test_ask_user_pause_resume.py`
4. **导入兼容**：现有 `from app.agent_loop_vnext.state import SingleImplementState` 等导入仍然有效。

## 9. 实施路线

### Phase 1（本次）：Agent 基类提取，单 Agent 流程跑通
1. 新建 `base/` 三件套（agent.py / state.py / result.py）
2. 新建 `agents/implementor/agent.py`，ImplementorAgent 继承 Agent
3. runner.py 精简为启动器
4. orchestrator.py 改调用 `run_vnext_agent`
5. state.py 兼容层
6. 全量测试验证功能等价

### Phase 2（后续）：Router Agent
1. 新建 `agents/router/`，RouterAgent 分析意图输出 RouteDecision
2. 启用 AgentRegistry，Router 读取 `list_agents()` 决策
3. orchestrator 先走 Router 再执行
4. single 模式验证

### Phase 3（后续）：Pipeline 引擎
1. 新建 `pipeline/executor.py` + `context_filter.py`
2. 实现 ContextFilter（分层裁剪）
3. Router 可返回 pipeline 路径
4. Pipeline 暂停/恢复支持

### Phase 4（后续）：新 Agent
1. Planner Agent
2. Validator Agent
3. Reviewer / Architect 按需

## 10. 与 legacy 引擎的边界（强制）

- **不复用 legacy 任何代码**：`agent_loop/` 下的 `agents/base.py`（ImplementAgent ABC）、`agents/application.py`、`PromptModule/PromptComposer` 体系一概不参考。
- **vNext 自包含**：`shared/resume_answers.py` 已自包含（不依赖 `app.agent_loop.resume_answers`），保持这一原则。
- **Agent 基类独立设计**：`base/agent.py` 的 Agent ABC 与 legacy 的 `ImplementAgent` 无任何继承或引用关系。
- **命名约定**：vNext 的 Agent 体系内部统一用 `Agent` / `AgentRunState` / `AgentResult`，不沿用 legacy 的 `ImplementAgent` / `AgentLoopState` 命名。
