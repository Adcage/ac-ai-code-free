"""Agent 体系工具基类，继承 LangChain BaseTool 并扩展。"""

from langchain_core.tools import BaseTool
from pydantic import ConfigDict


class AgentTool(BaseTool):
    """Agent 体系工具基类，继承 LangChain BaseTool 并扩展。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # 工具元信息，用于历史记录和事件映射
    tool_id: str = ""  # 默认取 name，可显式指定

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("Use _arun (async) instead")

    def rebuild_history_context(self, record) -> str:
        """从历史记录重建工具调用的上下文。

        默认实现：直接返回存储的结果。
        需要特殊处理的工具（如 view 重新读取文件）override 此方法。

        当前阶段不调用，预留扩展点。
        """
        return getattr(record, "result", "") or ""
