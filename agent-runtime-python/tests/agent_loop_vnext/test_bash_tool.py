"""BashTool 单元测试。"""

import os
import tempfile

import pytest

from app.agent_loop_vnext.shared.tools.bash_tool import (
    ALLOWED_COMMANDS,
    BashTool,
)
from app.core.error_codes import AgentErrorCode
from app.core.exceptions import AgentRuntimeError
from app.tools.file_tools import FileTools, Workspace


@pytest.fixture
def workspace():
    """创建临时工作区。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Workspace(tmpdir)


@pytest.fixture
def bash_tool(workspace):
    """创建 BashTool 实例。"""
    file_tools = FileTools(workspace)
    return BashTool(file_tools=file_tools)


# --- 正常执行 ---


@pytest.mark.asyncio
async def test_bash_runs_allowed_command(bash_tool):
    """node -e "console.log('hello')" 正常执行。"""
    result = await bash_tool._arun(command='node -e "console.log(\'hello\')"')
    assert "[exit_code=0]" in result
    assert "hello" in result


@pytest.mark.asyncio
async def test_bash_runs_npm_version(bash_tool):
    """npm --version 正常执行。"""
    result = await bash_tool._arun(command="npm --version")
    assert "[exit_code=0]" in result


@pytest.mark.asyncio
async def test_bash_exit_code_nonzero(bash_tool):
    """命令失败时返回非零 exit_code。"""
    result = await bash_tool._arun(command="node -e \"process.exit(1)\"")
    assert "[exit_code=1]" in result


# --- 白名单拒绝 ---


@pytest.mark.asyncio
async def test_bash_rejects_disallowed_command(bash_tool):
    """rm 不在白名单，抛 COMMAND_NOT_ALLOWED。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="rm -rf /")
    assert exc_info.value.code == AgentErrorCode.COMMAND_NOT_ALLOWED


@pytest.mark.asyncio
async def test_bash_rejects_git(bash_tool):
    """git 不在白名单。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="git status")
    assert exc_info.value.code == AgentErrorCode.COMMAND_NOT_ALLOWED


@pytest.mark.asyncio
async def test_bash_rejects_curl(bash_tool):
    """curl 不在白名单。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="curl http://example.com")
    assert exc_info.value.code == AgentErrorCode.COMMAND_NOT_ALLOWED


# --- Shell 注入拦截 ---


@pytest.mark.asyncio
async def test_bash_rejects_and_operator(bash_tool):
    """&& 操作符被拒绝。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="npm install && npm run build")
    assert exc_info.value.code == AgentErrorCode.COMMAND_INJECTION_BLOCKED


@pytest.mark.asyncio
async def test_bash_rejects_pipe_operator(bash_tool):
    """| 管道被拒绝。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="node -e \"console.log(1)\" | cat")
    assert exc_info.value.code == AgentErrorCode.COMMAND_INJECTION_BLOCKED


@pytest.mark.asyncio
async def test_bash_rejects_semicolon(bash_tool):
    """; 分号被拒绝。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="npm install ; rm -rf /")
    assert exc_info.value.code == AgentErrorCode.COMMAND_INJECTION_BLOCKED


@pytest.mark.asyncio
async def test_bash_rejects_subcommand(bash_tool):
    """$() 命令替换被拒绝。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="node -e \"$(cat /etc/passwd)\"")
    assert exc_info.value.code == AgentErrorCode.COMMAND_INJECTION_BLOCKED


# --- 高危子命令 ---


@pytest.mark.asyncio
async def test_bash_rejects_dangerous_python_inline(bash_tool):
    """python -c 含 os.system 被拒绝。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command='python -c "import os; os.system(\'rm -rf /\')"')
    assert exc_info.value.code == AgentErrorCode.COMMAND_INJECTION_BLOCKED


@pytest.mark.asyncio
async def test_bash_rejects_dangerous_python_subprocess(bash_tool):
    """python -c 含 subprocess 被拒绝。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command='python -c "import subprocess"')
    assert exc_info.value.code == AgentErrorCode.COMMAND_INJECTION_BLOCKED


@pytest.mark.asyncio
async def test_bash_rejects_dangerous_node_inline(bash_tool):
    """node -e 含 child_process 被拒绝。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command='node -e "require(\'child_process\')"')
    assert exc_info.value.code == AgentErrorCode.COMMAND_INJECTION_BLOCKED


@pytest.mark.asyncio
async def test_bash_rejects_npm_publish(bash_tool):
    """npm publish 被拒绝。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="npm publish")
    assert exc_info.value.code == AgentErrorCode.COMMAND_INJECTION_BLOCKED


@pytest.mark.asyncio
async def test_bash_allows_safe_python_script(bash_tool, workspace):
    """python script.py（非 -c）允许执行。"""
    # 创建一个简单的脚本
    script_path = os.path.join(workspace.root, "test_script.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("print('safe')\n")
    result = await bash_tool._arun(command="python test_script.py")
    assert "[exit_code=0]" in result
    assert "safe" in result


# --- 空命令 ---


@pytest.mark.asyncio
async def test_bash_empty_command(bash_tool):
    """空命令抛 TOOL_ARGS_ERROR。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="")
    assert exc_info.value.code == AgentErrorCode.TOOL_ARGS_ERROR


@pytest.mark.asyncio
async def test_bash_whitespace_command(bash_tool):
    """纯空白命令抛 TOOL_ARGS_ERROR。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(command="   ")
    assert exc_info.value.code == AgentErrorCode.TOOL_ARGS_ERROR


# --- 超时 ---


@pytest.mark.asyncio
async def test_bash_timeout(bash_tool):
    """超时命令抛 COMMAND_TIMEOUT。"""
    with pytest.raises(AgentRuntimeError) as exc_info:
        await bash_tool._arun(
            command='node -e "setTimeout(() => {}, 60000)"',
            timeout=1,
        )
    assert exc_info.value.code == AgentErrorCode.COMMAND_TIMEOUT


# --- 输出截断 ---


@pytest.mark.asyncio
async def test_bash_output_truncation(bash_tool):
    """超长输出被截断。"""
    # 生成超过 10KB 的输出
    result = await bash_tool._arun(
        command='node -e "console.log(\'x\'.repeat(15000))"'
    )
    assert "[exit_code=0]" in result
    assert "输出已截断" in result


# --- 工作目录 ---


@pytest.mark.asyncio
async def test_bash_runs_in_workspace(bash_tool, workspace):
    """命令在工作区目录中执行。"""
    result = await bash_tool._arun(command="node -e \"console.log(process.cwd())\"")
    assert "[exit_code=0]" in result
    # 工作目录应该是 workspace.root
    assert os.path.normpath(workspace.root) in result or workspace.root in result


# --- 白名单内容 ---


def test_allowed_commands():
    """验证白名单包含预期命令。"""
    assert ALLOWED_COMMANDS == frozenset({"npm", "npx", "node", "pip", "python"})
