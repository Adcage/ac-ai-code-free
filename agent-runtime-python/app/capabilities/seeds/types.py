from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SeedDefinition:
    id: str
    name: str
    description: str
    code_gen_type: str
    entry: str
    files_dir: Path
    copy_mode: str
    source_path: Path
