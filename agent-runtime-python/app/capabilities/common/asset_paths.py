from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssetPathConfig:
    bundled_root: Path
    project_root: Path | None = None
    user_root: Path | None = None

    def roots_by_priority(self) -> tuple[Path, ...]:
        roots: list[Path] = []
        if self.project_root is not None:
            roots.append(self.project_root)
        if self.user_root is not None:
            roots.append(self.user_root)
        roots.append(self.bundled_root)
        return tuple(roots)
