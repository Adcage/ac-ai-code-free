from abc import ABC, abstractmethod
from typing import Any


class PromptModule(ABC):
    id: str = ""

    def enabled(self, context: Any, state: Any) -> bool:
        return True

    @abstractmethod
    def render(self, context: Any, state: Any) -> str:
        raise NotImplementedError
