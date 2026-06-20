import logging

from app.capabilities.skills.registry import SkillRegistry
from app.capabilities.skills.types import SkillDefinition

logger = logging.getLogger("app.capabilities.skills.selector")


class SkillSelector:
    def select(self, prompt: str, registry: SkillRegistry) -> list[SkillDefinition]:
        all_skills = registry.all()
        return sorted(all_skills, key=lambda s: s.name)
