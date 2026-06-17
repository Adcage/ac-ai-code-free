from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SkillDefinition:
    id: str
    name: str
    description: str
    body: str
    source_path: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    references: tuple[str, ...] = ()
