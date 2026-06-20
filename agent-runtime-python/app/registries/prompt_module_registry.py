import logging

from app.prompts.modules import PromptModule

logger = logging.getLogger("app.registries.prompt_module_registry")


class PromptModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, PromptModule] = {}
        self._order: list[str] = []

    def register(self, module: PromptModule) -> None:
        if module.id in self._modules:
            raise ValueError(f"Duplicate prompt module id: {module.id}")
        self._modules[module.id] = module
        self._order.append(module.id)
        logger.info("registered prompt module | id=%s", module.id)

    def get(self, module_id: str) -> PromptModule:
        if module_id not in self._modules:
            raise KeyError(f"Prompt module not registered: {module_id}")
        return self._modules[module_id]

    def ordered_modules(self) -> list[PromptModule]:
        return [self._modules[mid] for mid in self._order if mid in self._modules]
