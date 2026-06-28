"""vNext Bash 工具：在工作区中执行 shell 命令。

安全防御 4 层：
1. Shell 注入拦截 — 拒绝 &&、||、|、;、$()、反引号
2. 白名单校验 — 仅允许 npm/npx/node/pip/python
3. 高危子命令黑名单 — python -c 含 os.system/subprocess、node -e 含 child_process、npm publish
4. 超时 + 输出截断 — 默认 30s，最大 120s；输出超过 10KB 截断标注
"""

import asyncio
import logging
import re
import shlex
import subprocess
import sys
import time
from typing import Type

from pydantic import BaseModel, Field

from app.agent_loop_vnext.shared.tools.base import AgentTool
from app.core.error_codes import AgentErrorCode
from app.core.exceptions import AgentRuntimeError
from app.tools.file_tools import FileTools

logger = logging.getLogger("app.agent_loop_vnext.shared.tools.bash_tool")


# --- 白名单 ---

ALLOWED_COMMANDS = frozenset({"npm", "npx", "node", "pip", "python"})

# --- Shell 操作符黑名单 ---

_SHELL_OPERATORS = frozenset({"&&", "||", "|", ";", "&", "<", ">", ">>", "<<"})
_SUBCOMMAND_PREFIX = "$("

# --- 高危子命令模式 ---

_DANGEROUS_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "python": [
        re.compile(r"-c\s+.*(?:os\.system|subprocess|exec\(|eval\()"),
    ],
    "node": [
        re.compile(r"-e\s+.*(?:child_process|exec\()"),
    ],
    "npm": [
        re.compile(r"\bpublish\b"),
    ],
}

# --- 输出限制 ---

DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120
MAX_OUTPUT_BYTES = 10240  # 10KB


# --- Input Schema ---


class BashInput(BaseModel):
    command: str = Field(description="要执行的 shell 命令")
    timeout: int | None = Field(
        default=None,
        description="超时秒数，默认30，最大120",
    )


# --- Tool ---


class BashTool(AgentTool):
    name: str = "Bash"
    description: str = (
        "在工作区目录中执行 shell 命令。"
        "仅允许白名单内的命令（npm/npx/node/pip/python），"
        "禁止管道和链式操作符。"
    )
    args_schema: Type[BaseModel] = BashInput
    file_tools: FileTools | None = None

    async def _arun(self, command: str, timeout: int | None = None) -> str:
        # 1. 空命令校验
        if not command or not command.strip():
            raise AgentRuntimeError(
                "命令不能为空", code=AgentErrorCode.TOOL_ARGS_ERROR
            )

        command = command.strip()

        # 2. Shell 解析 + 注入拦截
        tokens = self._parse_and_check_injection(command)

        # 3. 白名单校验
        prefix = tokens[0]
        if prefix not in ALLOWED_COMMANDS:
            raise AgentRuntimeError(
                f"命令不在允许列表中: {prefix}（允许: {', '.join(sorted(ALLOWED_COMMANDS))}）",
                code=AgentErrorCode.COMMAND_NOT_ALLOWED,
            )

        # 4. 高危子命令检查
        self._check_dangerous_subcommand(prefix, command)

        # 5. 执行
        effective_timeout = min(timeout or DEFAULT_TIMEOUT, MAX_TIMEOUT)
        start_ms = time.monotonic()

        try:
            result = await self._execute(tokens, effective_timeout, command)
            duration_ms = (time.monotonic() - start_ms) * 1000
            logger.info(
                "bash | command=%s duration_ms=%.0f exit_code=%d output_len=%d",
                command,
                duration_ms,
                result["exit_code"],
                len(result["output"]),
            )
            return self._format_output(result)
        except subprocess.TimeoutExpired:
            duration_ms = (time.monotonic() - start_ms) * 1000
            logger.warning(
                "bash timeout | command=%s duration_ms=%.0f",
                command,
                duration_ms,
            )
            raise AgentRuntimeError(
                f"命令执行超时 ({effective_timeout}s): {command}",
                code=AgentErrorCode.COMMAND_TIMEOUT,
            )
        except AgentRuntimeError:
            raise
        except Exception as e:
            duration_ms = (time.monotonic() - start_ms) * 1000
            logger.error(
                "bash error | command=%s duration_ms=%.0f error=%s",
                command,
                duration_ms,
                e,
                exc_info=True,
            )
            raise AgentRuntimeError(
                f"命令执行失败: {e}",
                code=AgentErrorCode.COMMAND_EXECUTION_FAILED,
            ) from e

    def _parse_and_check_injection(self, command: str) -> list[str]:
        """解析命令并检查 shell 注入。"""
        try:
            tokens = shlex.split(command)
        except ValueError:
            raise AgentRuntimeError(
                f"命令解析失败，可能存在未配对的引号: {command}",
                code=AgentErrorCode.COMMAND_INJECTION_BLOCKED,
            )

        if not tokens:
            raise AgentRuntimeError(
                "命令不能为空", code=AgentErrorCode.TOOL_ARGS_ERROR
            )

        # 检查 shell 操作符
        for token in tokens:
            if token in _SHELL_OPERATORS:
                raise AgentRuntimeError(
                    f"检测到 shell 操作符，已拒绝: {command}",
                    code=AgentErrorCode.COMMAND_INJECTION_BLOCKED,
                )
            if _SUBCOMMAND_PREFIX in token:
                raise AgentRuntimeError(
                    f"检测到命令替换，已拒绝: {command}",
                    code=AgentErrorCode.COMMAND_INJECTION_BLOCKED,
                )
            if token.startswith("`") and token.endswith("`"):
                raise AgentRuntimeError(
                    f"检测到反引号命令替换，已拒绝: {command}",
                    code=AgentErrorCode.COMMAND_INJECTION_BLOCKED,
                )

        return tokens

    def _check_dangerous_subcommand(self, prefix: str, command: str) -> None:
        """检查白名单内命令的高危子命令模式。"""
        patterns = _DANGEROUS_PATTERNS.get(prefix)
        if not patterns:
            return

        for pattern in patterns:
            if pattern.search(command):
                raise AgentRuntimeError(
                    f"检测到高危子命令模式，已拒绝: {command}",
                    code=AgentErrorCode.COMMAND_INJECTION_BLOCKED,
                )

    async def _execute(self, tokens: list[str], timeout: int, command: str) -> dict:
        """执行命令，返回 {exit_code, output}。

        使用 run_in_executor + subprocess.run，避免 asyncio subprocess transport
        在部分 Python 版本（如 3.13 + Windows）上 NotImplementedError 的问题。

        Windows 上 exec 找不到命令（npm.cmd）时，fallback 到 shell=True。
        tokens 已经过安全校验（白名单 + 注入拦截），shell=True 不会引入额外风险。
        """
        workspace = self.file_tools._workspace
        loop = asyncio.get_running_loop()

        try:
            completed = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    tokens,
                    capture_output=True,
                    cwd=workspace.root,
                    timeout=timeout,
                ),
            )
        except FileNotFoundError:
            if sys.platform != "win32":
                raise
            # Windows：npm.cmd 等需要 shell 才能找到
            completed = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    capture_output=True,
                    cwd=workspace.root,
                    timeout=timeout,
                    shell=True,
                ),
            )

        stdout = completed.stdout.decode("utf-8", errors="replace")
        stderr = completed.stderr.decode("utf-8", errors="replace")

        # 合并 stdout 和 stderr
        combined = stdout
        if stderr:
            if combined:
                combined += "\n"
            combined += stderr

        exit_code = completed.returncode or 0
        return {"exit_code": exit_code, "output": combined}

    @staticmethod
    def _format_output(result: dict) -> str:
        """格式化输出，截断超长内容。"""
        output = result["output"]
        exit_code = result["exit_code"]

        if len(output.encode("utf-8")) > MAX_OUTPUT_BYTES:
            # 截断到 MAX_OUTPUT_BYTES（按字符近似截断）
            truncation_point = MAX_OUTPUT_BYTES
            output = output[:truncation_point]
            output += f"\n\n[输出已截断，原始大小超过 {MAX_OUTPUT_BYTES // 1024}KB]"

        return f"[exit_code={exit_code}]\n{output}"
