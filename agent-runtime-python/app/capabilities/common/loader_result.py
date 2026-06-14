from dataclasses import dataclass, field
from typing import Any


@dataclass
class SelectedCapabilities:
    skill: Any = None
    seed: Any = None
    template: Any = None
    design_system: Any = None
    craft: list[Any] = field(default_factory=list)
