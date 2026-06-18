import logging

from app.prompts.modules import PromptModule

logger = logging.getLogger("app.prompts.registry")


class PromptModuleRegistry:
    """提示词模块注册中心，管理所有 PromptModule 实例的注册和查询。"""

    def __init__(self) -> None:
        self._modules: list[PromptModule] = []

    def register(self, module: PromptModule) -> None:
        """注册一个提示词模块，按注册顺序排列。"""
        existing = self.get_by_id(module.id)
        if existing is not None:
            logger.warning("register | module %s already registered, skipping duplicate", module.id)
            return
        self._modules.append(module)
        logger.debug("register | module=%s category=%s", module.id, module.category)

    def ordered_modules(self) -> list[PromptModule]:
        """按注册顺序返回所有模块。"""
        return list(self._modules)

    def get_by_id(self, module_id: str) -> PromptModule | None:
        """按 ID 查找模块。"""
        for m in self._modules:
            if m.id == module_id:
                return m
        return None

    def modules_by_category(self, category: str) -> list[PromptModule]:
        """按类别筛选模块。"""
        return [m for m in self._modules if m.category == category]
