from dataclasses import dataclass, field


@dataclass(frozen=True)
class LoadedSkill:
    """已加载的 Skill 摘要，供 Read 工具解析 skill/ 前缀路径。"""

    skill_id: str
    name: str
    description: str
    source_dir: str  # Skill 目录的绝对路径
    references: tuple[str, ...] = ()


@dataclass
class SingleImplementState:
    """vNext 最小状态，只跟踪运行进度。"""

    status: str = "running"  # running | completed | failed | waiting_for_user
    iteration: int = 0
    loaded_skills: dict[str, LoadedSkill] = field(default_factory=dict)
    pending_question: dict | None = None  # ask_user 暂停时保存的问题结构，仅运行时使用
