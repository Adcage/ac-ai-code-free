"""测试 ImplementorPromptBuilder 提示词构建。"""

from app.agent_loop_vnext.agents.implementor.prompt import ImplementorPromptBuilder
from app.agent_loop_vnext.state import SingleImplementState
from app.runtime.context import CodeGenType, ExecutionContext, RunMode


def _make_context(code_gen_type: CodeGenType = CodeGenType.VUE_PROJECT) -> ExecutionContext:
    return ExecutionContext(
        agent_run_id=1, app_id=1, session_id=1, user_id=1,
        prompt="写一个登录页",
        code_gen_type=code_gen_type,
        workspace_path="/tmp/test",
        run_mode=RunMode.GENERATE,
    )


def test_build_system_prompt_contains_role():
    """系统提示词应包含角色定义。"""
    builder = ImplementorPromptBuilder(_make_context(), SingleImplementState())
    prompt = builder.build_system_prompt()
    assert "代码实现助手" in prompt
    assert "仔细理解用户需求" in prompt


def test_project_rules_single_file():
    """single_file 模式应包含单文件规则。"""
    context = _make_context(CodeGenType.SINGLE_FILE)
    builder = ImplementorPromptBuilder(context, SingleImplementState())
    prompt = builder.build_system_prompt()
    assert "单文件模式" in prompt
    assert "index.html" in prompt


def test_project_rules_multi_file():
    """multi-file 模式应包含多文件规则。"""
    context = _make_context(CodeGenType.MULTI_FILE)
    builder = ImplementorPromptBuilder(context, SingleImplementState())
    prompt = builder.build_system_prompt()
    assert "多文件模式" in prompt
    assert "index.html" in prompt
    assert "style.css" in prompt
    assert "script.js" in prompt


def test_project_rules_vue_project():
    """vue_project 模式应包含 Vue 项目规则。"""
    context = _make_context(CodeGenType.VUE_PROJECT)
    builder = ImplementorPromptBuilder(context, SingleImplementState())
    prompt = builder.build_system_prompt()
    assert "Vue 工程模式" in prompt
    assert "vue-router" in prompt


def test_project_rules_unknown():
    """未知 code_gen_type 应显示类型值。"""
    context = _make_context("unknown_type")  # type: ignore
    builder = ImplementorPromptBuilder(context, SingleImplementState())
    prompt = builder.build_system_prompt()
    assert "unknown_type" in prompt
