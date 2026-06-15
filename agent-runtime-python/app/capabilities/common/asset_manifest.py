import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AssetManifest:
    enabled_skills: set[str] = field(default_factory=set)
    enabled_seeds: set[str] = field(default_factory=set)
    enabled_templates: set[str] = field(default_factory=set)
    enabled_design_systems: set[str] = field(default_factory=set)
    enabled_craft: set[str] = field(default_factory=set)
    aliases: dict[str, dict[str, str]] = field(default_factory=dict)
    defaults: dict[str, dict[str, Any]] = field(default_factory=dict)

    def is_enabled(self, kind: str, asset_id: str) -> bool:
        enabled_by_kind = {
            "skills": self.enabled_skills,
            "seeds": self.enabled_seeds,
            "templates": self.enabled_templates,
            "design-systems": self.enabled_design_systems,
            "craft": self.enabled_craft,
        }
        enabled = enabled_by_kind.get(kind, set())
        return not enabled or asset_id in enabled

    def resolve_alias(self, kind: str, asset_id: str) -> str:
        return self.aliases.get(kind, {}).get(asset_id, asset_id)


def load_asset_manifest(root: Path) -> AssetManifest:
    manifest_path = root / "asset-manifest.json"
    if not manifest_path.is_file():
        return AssetManifest()

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    enabled = data.get("enabled", {})
    aliases = data.get("aliases", {})
    defaults = data.get("defaults", {})

    return AssetManifest(
        enabled_skills=set(enabled.get("skills", [])),
        enabled_seeds=set(enabled.get("seeds", [])),
        enabled_templates=set(enabled.get("templates", [])),
        enabled_design_systems=set(enabled.get("designSystems", [])),
        enabled_craft=set(enabled.get("craft", [])),
        aliases=aliases if isinstance(aliases, dict) else {},
        defaults=defaults if isinstance(defaults, dict) else {},
    )
