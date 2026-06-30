"""DelegateToAgentTool — 通用子 Agent 派遣工具。

可用于 Conductor 或其他需要调度子 Agent 的场景。
"""

import logging
import uuid
from typing import Any, Type

from pydantic import BaseModel, Field

from app.agent_loop_vnext.agents import AgentRegistry
from app.agent_loop_vnext.agents.conductor.templates import TASK_TEMPLATES
from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.runtime.context import ExecutionContext
from app.runtime.services import RuntimeServices

logger = logging.getLogger("app.agent_loop_vnext.shared.tools.delegate_tool")


class DelegateInput(BaseModel):
    agent_name: str = Field(description="要派遣的子 Agent 名称")
    task: str = Field(
        default="",
        description='PM 的补充说明。系统模板已经包含用户需求，请写需要额外提醒的重点（如"用户强调首屏速度"），需求无补充则传空串',
    )


class DelegateToAgentTool(AgentTool):
    """将任务派遣给指定 Agent 执行。"""

    model_config = {"arbitrary_types_allowed": True}

    name: str = "delegate_to_agent"
    description: str = "将任务派遣给指定子 Agent，等待其完成后返回结果摘要"
    args_schema: Type[BaseModel] = DelegateInput

    agent_registry: type[AgentRegistry] | None = None
    services: RuntimeServices | None = None
    parent_context: ExecutionContext | None = None
    user_prompt: str = ""
    conductor_state: Any | None = None  # ConductorState，运行时注入
    _accumulated_summary: str = ""  # 前序 Agent 的累积摘要，跨调用持久

    async def _arun(self, agent_name: str, task: str = "") -> str:
        if self.agent_registry is None:
            return "错误：未绑定 AgentRegistry"
        if not self.agent_registry.has(agent_name):
            available = [a["name"] for a in self.agent_registry.list_agents()]
            return f"错误：Agent '{agent_name}' 不存在。可选: {', '.join(available)}"

        agent = self.agent_registry.get(agent_name)

        # 拼接系统模板 + PM 补充 + 前序摘要
        template = TASK_TEMPLATES.get(agent_name, "")
        if template:
            prev_summary = ""
            if self._accumulated_summary:
                prev_summary = f"## 前序工作\n{self._accumulated_summary}\n"
            full_task = template.format(
                user_prompt=self.user_prompt,
                pm_notes=task,
                previous_summary=prev_summary,
            )
        else:
            full_task = task or self.user_prompt

        # 构造子上下文
        sub_context = ExecutionContext(
            agent_run_id=uuid.uuid4().int & 0x7FFFFFFFFFFFFFFF,
            app_id=self.parent_context.app_id,
            session_id=self.parent_context.session_id,
            user_id=self.parent_context.user_id,
            prompt=full_task,
            code_gen_type=self.parent_context.code_gen_type,
            workspace_path=self.parent_context.workspace_path,
            run_mode=self.parent_context.run_mode,
            chat_history=(),
            attachments=self.parent_context.attachments,
            runtime_options={
                **self.parent_context.runtime_options,
                "_parent_agent": "conductor",
            },
        )

        logger.info(
            "delegate_to_agent | agent=%s task_len=%d",
            agent_name,
            len(task),
        )

        # 发射 AGENT_START 事件（前端展示阶段切换）
        if self.services and hasattr(self.services, "event_bus") and self.services.event_bus:
            from app.runtime.events import RuntimeEvent, RuntimeEventType

            await self.services.event_bus.emit(RuntimeEvent(
                RuntimeEventType.AGENT_START,
                {"agent_name": agent_name},
            ))

        # 执行子 Agent
        result = await agent.run(sub_context, self.services)

        # 处理 needs_clarification
        if result.status == "needs_clarification":
            if self.conductor_state is not None:
                self.conductor_state.phase = "needs_clarification"
                self.conductor_state.needs_revision = result.message
            return f"规划任务无法完成，原因：{result.message}"

        # 累积前序摘要（供后续 Agent 使用）
        summary = result.message or "任务完成"
        if summary:
            agent_label = {"planner": "规划", "implementor": "实现", "validator": "校验"}.get(agent_name, agent_name)
            self._accumulated_summary += f"- {agent_label}完成：{summary}\n"

        return summary
