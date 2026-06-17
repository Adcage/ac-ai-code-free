import logging

from app.capabilities.craft.registry import CraftRegistry
from app.capabilities.craft.types import CraftDefinition

logger = logging.getLogger("app.capabilities.craft.selector")

DEFAULT_CRAFT_IDS: tuple[str, ...] = ("anti-ai-slop", "state-coverage")


class CraftSelector:
    def select(
        self,
        code_gen_type: str,
        registry: CraftRegistry,
        required_craft_ids: tuple[str, ...] = (),
        suggested_craft_ids: tuple[str, ...] = (),
        default_craft_ids: tuple[str, ...] | None = None,
    ) -> tuple[CraftDefinition, ...]:
        candidate_ids: list[str] = []

        for craft_id in required_craft_ids:
            if craft_id not in candidate_ids:
                candidate_ids.append(craft_id)

        for craft_id in suggested_craft_ids:
            if craft_id not in candidate_ids:
                candidate_ids.append(craft_id)

        defaults = default_craft_ids if default_craft_ids is not None else DEFAULT_CRAFT_IDS
        for craft_id in defaults:
            if craft_id not in candidate_ids:
                candidate_ids.append(craft_id)

        resolved: list[CraftDefinition] = []
        for craft_id in candidate_ids:
            try:
                craft = registry.get(craft_id)
            except KeyError:
                logger.warning("Craft id not found in registry, skipping: %s", craft_id)
                continue

            if craft.applies_to and code_gen_type not in craft.applies_to:
                continue

            resolved.append(craft)

        resolved.sort(key=lambda c: c.priority)
        return tuple(resolved)
