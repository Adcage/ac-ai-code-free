import logging

from app.capabilities.craft.types import CraftDefinition
from app.prompts.modules import PromptModule

logger = logging.getLogger("app.capabilities.craft.prompt_module")


class CraftRulesModule(PromptModule):
    id = "craft_rules"

    def __init__(self, crafts: tuple[CraftDefinition, ...] = ()) -> None:
        self._crafts = crafts

    def enabled(self, context: object, state: object) -> bool:
        return len(self._crafts) > 0

    def render(self, context: object, state: object) -> str:
        sections: list[str] = []
        seen_ids: set[str] = set()

        for craft in self._crafts:
            if craft.id in seen_ids:
                continue
            seen_ids.add(craft.id)

            if not craft.body.strip():
                continue

            sections.append(f"## Craft: {craft.name}")
            sections.append(craft.body.strip())

        if not sections:
            return ""

        return "\n\n".join(sections)
