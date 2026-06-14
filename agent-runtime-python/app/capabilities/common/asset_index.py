import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.capabilities.common.asset_paths import AssetPathConfig
from app.capabilities.craft.loader import CraftLoader
from app.capabilities.craft.registry import CraftRegistry
from app.capabilities.design_systems.loader import DesignSystemLoader
from app.capabilities.design_systems.registry import DesignSystemRegistry
from app.capabilities.seeds.loader import SeedLoader
from app.capabilities.seeds.registry import SeedRegistry
from app.capabilities.skills.loader import SkillLoader
from app.capabilities.skills.registry import SkillRegistry
from app.capabilities.templates.loader import TemplateLoader
from app.capabilities.templates.registry import TemplateRegistry

logger = logging.getLogger("app.capabilities.common.asset_index")


@dataclass
class AssetIndex:
    skill_registry: SkillRegistry
    seed_registry: SeedRegistry
    template_registry: TemplateRegistry
    design_system_registry: DesignSystemRegistry
    craft_registry: CraftRegistry


@dataclass
class _LoaderBundle:
    skill: SkillLoader = field(default_factory=SkillLoader)
    seed: SeedLoader = field(default_factory=SeedLoader)
    template: TemplateLoader = field(default_factory=TemplateLoader)
    design_system: DesignSystemLoader = field(default_factory=DesignSystemLoader)
    craft: CraftLoader = field(default_factory=CraftLoader)


class AssetManager:
    def __init__(self, path_config: AssetPathConfig, loaders: _LoaderBundle | None = None) -> None:
        self._path_config = path_config
        self._loaders = loaders or _LoaderBundle()
        self._index: AssetIndex | None = None

    def get_index(self) -> AssetIndex:
        if self._index is None:
            self._index = self.refresh()
        return self._index

    def refresh(self) -> AssetIndex:
        index = AssetIndex(
            skill_registry=self._loaders.skill.load(self._path_config),
            seed_registry=self._loaders.seed.load(self._path_config),
            template_registry=self._loaders.template.load(self._path_config),
            design_system_registry=self._loaders.design_system.load(self._path_config),
            craft_registry=self._loaders.craft.load(self._path_config),
        )
        self._index = index
        return index


def create_default_asset_manager() -> AssetManager:
    bundled_root = Path(__file__).parent.parent.parent / "assets"
    path_config = AssetPathConfig(bundled_root=bundled_root)
    return AssetManager(path_config=path_config)
