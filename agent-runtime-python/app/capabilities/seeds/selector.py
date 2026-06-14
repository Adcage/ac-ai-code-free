import logging

from app.capabilities.seeds.registry import SeedRegistry
from app.capabilities.seeds.types import SeedDefinition

logger = logging.getLogger("app.capabilities.seeds.selector")

VUE_PROJECT_DEFAULT_SEED = "vue-basic"


class SeedSelector:
    def select(
        self,
        prompt: str,
        code_gen_type: str,
        run_mode: str,
        registry: SeedRegistry,
    ) -> SeedDefinition | None:
        if run_mode != "generate":
            return None

        prompt_lower = prompt.lower()
        candidates: list[tuple[int, str, SeedDefinition]] = []

        for seed in registry.all():
            if seed.code_gen_type != code_gen_type:
                continue
            score = sum(10 for trigger in seed.triggers if trigger.lower() in prompt_lower)
            if score > 0:
                candidates.append((score, seed.id, seed))

        if candidates:
            candidates.sort(key=lambda item: (-item[0], item[1]))
            return candidates[0][2]

        if code_gen_type == "vue_project":
            try:
                return registry.get(VUE_PROJECT_DEFAULT_SEED)
            except KeyError:
                logger.warning("Default vue-basic seed not found in registry")

        return None
