from abc import ABC, abstractmethod
from typing import Any, Literal


class PromptModule(ABC):
    id: str = ""
    category: Literal["mandatory", "strategic", "test"] = "strategic"

    def enabled(self, context: Any, state: Any) -> bool:
        # test 类模块的特殊处理
        if self.category == "test":
            # test_mode_info: 仅在 is_test=True 时启用
            if self.id == "test_mode_info":
                return bool(getattr(state, "is_test", False))
            # production_security: 仅在 is_test=False 时启用
            if self.id == "production_security":
                return not bool(getattr(state, "is_test", False))
            # 其他 test 类模块：默认在 is_test=True 时启用
            return bool(getattr(state, "is_test", False))
        # mandatory 类模块：始终启用
        if self.category == "mandatory":
            return True
        # strategic 类模块：子类自行判断
        return True

    @abstractmethod
    def render(self, context: Any, state: Any) -> str:
        raise NotImplementedError
