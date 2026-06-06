from pathlib import Path

from app.core.exceptions import AgentRuntimeError


class Workspace:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def resolve(self, relative_path: str) -> Path:
        if not relative_path or not relative_path.strip():
            raise AgentRuntimeError("文件路径不能为空")
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise AgentRuntimeError("文件路径越界")
        return candidate
