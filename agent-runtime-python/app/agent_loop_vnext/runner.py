"""vNext 单实现链路 Runner — SSE 对话传输 + 工具调用。

核心职责：
1. 创建 Workspace/FileTools（对话一开始就创建）
2. 构建系统提示词（使用 ImplementorPromptBuilder）
3. 构建消息列表（使用 HistoryBuilder，注入对话历史）
4. 绑定工具到模型
5. 流式调用模型 → 逐 chunk 发射 TEXT_DELTA → 处理 tool_calls → DONE
"""

import logging

from app.agent_loop_vnext.state import SingleImplementState
from app.core.config import settings
from app.core.error_codes import AgentErrorCode
from app.core.exceptions import AgentRuntimeError
from app.runtime.context import ExecutionContext
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.agent_loop_vnext.runner")


class SingleImplementLoopRunner:
    """vNext 单实现链路运行器。"""

    def __init__(self, context: ExecutionContext, services: RuntimeServices) -> None:
        self._context = context
        self._services = services
        self._state = SingleImplementState()
        self._event_bus = services.event_bus

    async def run(self) -> None:
        """执行 vNext 对话循环。"""
        from app.tools.file_tools import FileTools, Workspace

        # 1. 创建 Workspace（从 context.workspace_path，Java 传入）
        workspace = Workspace(self._context.workspace_path)
        file_tools = FileTools(workspace)

        # 2. 创建工具集（注入 file_tools）
        from app.agent_loop_vnext.agents.implementor.tools import create_implementor_tools
        tools = create_implementor_tools(file_tools)

        # 3. 解析模型配置
        await self._services.model_resolver.load_bundle(self._context)
        from app.modeling.roles import ModelRole
        resolved = self._services.model_resolver.resolve(ModelRole.PRIMARY)
        chat_model = self._services.chat_model_factory.create({
            "provider": resolved.provider,
            "modelName": resolved.model_name,
            "apiKey": resolved.api_key,
            "baseUrl": resolved.base_url,
            "timeout": settings.model_request_timeout,
        })

        # 4. 构建系统提示词（使用 PromptBuilder）
        from app.agent_loop_vnext.agents.implementor.prompt import ImplementorPromptBuilder
        prompt_builder = ImplementorPromptBuilder(self._context, self._state)
        system_prompt = prompt_builder.build_system_prompt()

        # 5. 构建消息列表（使用 HistoryBuilder）
        from app.agent_loop_vnext.shared.history import HistoryBuilder
        history_builder = HistoryBuilder()
        messages = history_builder.build_messages(self._context, system_prompt)

        # 6. 绑定工具到模型
        chat_model_with_tools = chat_model.bind_tools(tools)

        try:
            # 7. 流式调用模型
            has_content = False
            async for chunk in chat_model_with_tools.astream(messages):
                # 处理文本内容
                text = getattr(chunk, "content", None)
                if text:
                    has_content = True
                    logger.debug("TEXT_DELTA chunk | length=%d", len(text))
                    await self._event_bus.emit(RuntimeEvent(
                        RuntimeEventType.TEXT_DELTA,
                        {"text": text},
                    ))

                # 处理工具调用
                tool_calls = getattr(chunk, "tool_calls", None)
                if tool_calls:
                    has_content = True
                    await self._handle_tool_calls(tool_calls, tools)

            if not has_content:
                await self._event_bus.emit(RuntimeEvent(
                    RuntimeEventType.RUNTIME_ERROR,
                    {"message": "模型返回为空", "code": int(AgentErrorCode.MODEL_RESPONSE_EMPTY)},
                ))

            # 完成
            self._state.status = "completed"
            await self._event_bus.emit(RuntimeEvent(
                RuntimeEventType.DONE,
                {"message": "对话完成"},
            ))

        except AgentRuntimeError as e:
            logger.error("vNext runner error: %s", e)
            await self._event_bus.emit(RuntimeEvent(
                RuntimeEventType.RUNTIME_ERROR,
                {"message": str(e), "code": int(e.code)},
            ))
            await self._event_bus.emit(RuntimeEvent(
                RuntimeEventType.DONE, {"message": f"失败: {e}"},
            ))
        except Exception as e:
            logger.error("vNext runner unexpected error: %s", e, exc_info=True)
            await self._event_bus.emit(RuntimeEvent(
                RuntimeEventType.RUNTIME_ERROR,
                {"message": str(e), "code": int(AgentErrorCode.INTERNAL_ERROR)},
            ))
            await self._event_bus.emit(RuntimeEvent(
                RuntimeEventType.DONE, {"message": f"异常: {e}"},
            ))

    async def _handle_tool_calls(self, tool_calls: list, tools: list) -> None:
        """处理模型触发的工具调用。"""
        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})
            tool_id = tc.get("id", "")

            logger.info("tool_call | name=%s id=%s", tool_name, tool_id)

            # 发射 TOOL_CALL 事件
            await self._event_bus.emit(RuntimeEvent(
                RuntimeEventType.TOOL_CALL,
                {
                    "id": tool_id,
                    "name": tool_name,
                    "arguments": tool_args,
                },
            ))

            # 查找匹配的工具并执行
            result = ""
            for tool in tools:
                if tool.name == tool_name:
                    try:
                        result = await tool._arun(**tool_args)
                    except Exception as e:
                        result = f"工具执行失败: {e}"
                    break

            # 发射 TOOL_RESULT 事件
            await self._event_bus.emit(RuntimeEvent(
                RuntimeEventType.TOOL_RESULT,
                {
                    "id": tool_id,
                    "name": tool_name,
                    "result": result,
                },
            ))
