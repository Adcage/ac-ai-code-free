import logging
from typing import Any

logger = logging.getLogger("app.registries.tool_registry")


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register(self, name: str, tool: Any) -> None:
        if name in self._tools:
            raise ValueError(f"Duplicate tool name: {name}")
        self._tools[name] = tool
        logger.info("registered tool | name=%s", name)

    def get(self, name: str) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool not registered: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def all_tools(self) -> list[Any]:
        return list(self._tools.values())
