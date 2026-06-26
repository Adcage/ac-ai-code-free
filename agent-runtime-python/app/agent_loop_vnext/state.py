from dataclasses import dataclass


@dataclass
class SingleImplementState:
    """vNext 最小状态，只跟踪运行进度。"""

    status: str = "running"  # running | completed | failed
    iteration: int = 0
