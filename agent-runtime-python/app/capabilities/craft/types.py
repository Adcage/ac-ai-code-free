from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CraftDefinition:
    id: str
    name: str
    description: str
    applies_to: tuple[str, ...]
    priority: int
    body: str
    source_path: Path
