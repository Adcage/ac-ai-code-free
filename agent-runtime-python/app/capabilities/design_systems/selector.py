import logging

from app.capabilities.design_systems.registry import DesignSystemRegistry
from app.capabilities.design_systems.types import DesignSystemDefinition

logger = logging.getLogger("app.capabilities.design_systems.selector")

DESIGN_SYSTEM_ID_HINTS: dict[str, str] = {
    "ant": "ant",
    "antd": "ant",
    "ant design": "ant",
    "enterprise": "enterprise",
    "clean": "clean",
    "dashboard": "dashboard",
}


class DesignSystemSelector:
    def select(
        self,
        prompt: str,
        code_gen_type: str,
        registry: DesignSystemRegistry,
        default_design_system_id: str = "",
    ) -> DesignSystemDefinition | None:
        all_ds = registry.all()
        if len(all_ds) == 0:
            return None

        hinted_id = self._extract_hinted_id(prompt)
        if hinted_id is not None:
            try:
                ds = registry.get(hinted_id)
                logger.info("Design system selected by prompt hint: %s", hinted_id)
                return ds
            except KeyError:
                logger.warning("Prompt hinted design system not found: %s", hinted_id)

        if default_design_system_id:
            try:
                ds = registry.get(default_design_system_id)
                logger.info("Design system selected by default: %s", default_design_system_id)
                return ds
            except KeyError:
                logger.warning("Default design system not found: %s", default_design_system_id)

        fallback = min(all_ds, key=lambda d: d.id)
        logger.info("Design system selected by fallback (smallest id): %s", fallback.id)
        return fallback

    def _extract_hinted_id(self, prompt: str) -> str | None:
        prompt_lower = prompt.lower()
        for hint, ds_id in DESIGN_SYSTEM_ID_HINTS.items():
            if hint in prompt_lower:
                return ds_id
        return None
