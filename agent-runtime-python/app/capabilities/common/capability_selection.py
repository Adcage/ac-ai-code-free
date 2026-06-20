from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilitySelection:
    skill_ids: tuple[str, ...] = ()
    seed_id: str = ""
    template_ids: tuple[str, ...] = ()
    design_system_id: str = ""
    craft_ids: tuple[str, ...] = ()
    project_mode: str = ""
    selection_source: str = "selector"
    confidence: float = 0.0
    reason: str = ""
    warnings: tuple[str, ...] = ()
