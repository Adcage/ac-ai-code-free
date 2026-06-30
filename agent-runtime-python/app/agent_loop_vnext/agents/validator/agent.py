"""Validator Agent — 代码校验师。"""

import logging
from typing import Any

from app.agent_loop_vnext.agents.validator.prompt import VALIDATOR_SYSTEM_PROMPT
from app.agent_loop_vnext.base.agent import Agent
from app.agent_loop_vnext.shared.tools.bash_tool import BashTool
from app.agent_loop_vnext.shared.tools.file_tools import (
    EditTool,
    GlobTool,
    GrepTool,
    ReadTool,
)
from app.tools.file_tools import FileTools

logger = logging.getLogger("app.agent_loop_vnext.agents.validator.agent")


class ValidatorAgent(Agent):
    """代码校验师：对照设计文档检查代码完整性，小问题直接修复。"""

    name = "validator"
    description = "校验代码完整性和质量"

    def __init__(self) -> None:
        super().__init__()

    def create_tools(
        self,
        file_tools: FileTools,
        services: Any,
    ) -> list[Any]:
        return [
            ReadTool(file_tools=file_tools),
            EditTool(file_tools=file_tools),
            GlobTool(file_tools=file_tools),
            GrepTool(file_tools=file_tools),
            BashTool(file_tools=file_tools),
        ]

    def build_system_prompt(
        self,
        context: Any,
        services: Any,
    ) -> str:
        return VALIDATOR_SYSTEM_PROMPT
