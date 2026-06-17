import logging

from app.capabilities.seeds.registry import SeedRegistry
from app.capabilities.seeds.types import SeedDefinition

logger = logging.getLogger("app.capabilities.seeds.selector")

VUE_PROJECT_DEFAULT_SEED = "vue-basic"


class SeedSelector:
    def select(
        self,
        code_gen_type: str,
        run_mode: str,
        registry: SeedRegistry,
        default_seed_id: str = "",
    ) -> SeedDefinition | None:
        if run_mode != "generate":
            return None

        if default_seed_id:
            try:
                seed = registry.get(default_seed_id)
                if seed.code_gen_type == code_gen_type:
                    return seed
            except KeyError:
                pass

        if code_gen_type == "vue_project":
            try:
                return registry.get(VUE_PROJECT_DEFAULT_SEED)
            except KeyError:
                logger.warning("Default vue-basic seed not found in registry")

        return None
