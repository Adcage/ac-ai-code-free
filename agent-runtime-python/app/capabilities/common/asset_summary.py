from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssetSummary:
    id: str
    kind: str
    name: str
    description: str
    when_to_use: str = ""
    triggers: tuple[str, ...] = ()
    code_gen_types: tuple[str, ...] = ()
    scenarios: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    source_path: str = ""
    metadata: dict[str, str] = field(default_factory=dict)
