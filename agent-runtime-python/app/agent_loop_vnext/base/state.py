from dataclasses import dataclass, field, asdict
import json


@dataclass(frozen=True)
class LoadedSkill:
    """已加载的 Skill 摘要，供 Read 工具解析 skill/ 前缀路径。"""

    skill_id: str
    name: str
    description: str
    source_dir: str  # Skill 目录的绝对路径
    references: tuple[str, ...] = ()


@dataclass
class ConductorState:
    """Conductor（指挥家）的运行状态。

    phase: 当前阶段
        - requirements: 需求分析阶段（AskUser 对话，需求确认后进入调度）
        - needs_clarification: Planner 反馈需求不清楚，等待重新澄清
        - scheduling: 调度阶段（派遣子 Agent 工作）
        - completed: 任务完成

    needs_revision: Planner 反馈的需求缺失说明，由 Conductor 转述给用户
    """

    phase: str = "requirements"
    needs_revision: str | None = None


@dataclass
class AgentRunState:
    """通用 Agent 运行状态。

    管理 Agent 的运行时状态、进度跟踪和 AskUser 暂停/恢复。
    """

    status: str = "running"  # running | completed | failed | waiting_for_user
    iteration: int = 0
    loaded_skills: dict[str, LoadedSkill] = field(default_factory=dict)
    pending_question: dict | None = None  # ask_user 暂停时保存的问题结构，仅运行时使用

    def serialize(self) -> str:
        """序列化为 JSON，供 AskUser 暂停时持久化。"""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    @classmethod
    def deserialize(cls, data: str) -> "AgentRunState":
        """从 JSON 反序列化。"""
        return cls(**json.loads(data))
