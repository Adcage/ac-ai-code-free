from dataclasses import dataclass, field
from typing import Any

from app.capabilities.common.capability_selection import CapabilitySelection


@dataclass
class SelectedCapabilities:
    selection: CapabilitySelection = field(default_factory=CapabilitySelection)
    skills: list[Any] = field(default_factory=list)
    seed: Any = None
    templates: list[Any] = field(default_factory=list)
    design_system: Any = None
    craft: list[Any] = field(default_factory=list)

    @property
    def skill(self) -> Any:
        return self.skills[0] if self.skills else None

    @property
    def template(self) -> Any:
        return self.templates[0] if self.templates else None
