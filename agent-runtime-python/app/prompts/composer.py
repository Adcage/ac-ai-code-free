import logging
from typing import Any

from app.prompts.modules import PromptModule

logger = logging.getLogger("app.prompts.composer")


class PromptComposer:
    def __init__(self, modules: list[PromptModule] | None = None) -> None:
        self._modules: list[PromptModule] = modules or []

    def add_module(self, module: PromptModule) -> None:
        self._modules.append(module)

    def compose(self, context: Any, state: Any) -> list[dict[str, str]]:
        system_parts: list[str] = []
        for module in self._modules:
            if module.enabled(context, state):
                rendered = module.render(context, state)
                if rendered and rendered.strip():
                    system_parts.append(rendered.strip())

        system_prompt = "\n\n".join(system_parts)
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": context.prompt})
        return messages
