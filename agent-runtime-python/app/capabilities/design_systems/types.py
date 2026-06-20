from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DesignSystemFiles:
    design: Path
    tokens: Path | None = None
    design_tokens: Path | None = None
    components_manifest: Path | None = None
    components: Path | None = None
    usage: Path | None = None


@dataclass(frozen=True)
class DesignSystemDefinition:
    id: str
    name: str
    category: str
    description: str
    import_mode: str
    files: DesignSystemFiles
    suggested_craft: tuple[str, ...] = ()
    source_path: Path = Path(".")
