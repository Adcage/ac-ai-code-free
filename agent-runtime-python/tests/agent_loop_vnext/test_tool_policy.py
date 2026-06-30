"""
Phase 0 Task 0-2: vNext 工具权限失败测试

本测试文件锁定 vNext 第一版工具白名单，防止后续 AI 顺手接入旧工具。

允许工具：
- read_dir, read_file, write_file, list_skills, load_skill, complete

禁止工具：
- ask_user, run_checks, run_command, decide_route, write_plan,
  complete_implementation, submit_validation_report, request_replan,
  confirm_design, select_skill, choose_skill

当前阶段：这些测试引用的模块尚不存在，预期因 ImportError 失败。
后续 Phase 2 实现后，这些测试必须通过。
"""

import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# 导入未来 vNext 模块 — Phase 0 阶段这些导入会失败，这是预期行为
# ---------------------------------------------------------------------------

try:
    from app.agent_loop_vnext.tools import build_vnext_tools
    from app.agent_loop_vnext.state import SingleImplementState

    _VNEXT_MODULES_AVAILABLE = True
except ImportError:
    _VNEXT_MODULES_AVAILABLE = False


# ---------------------------------------------------------------------------
# 常量：工具白名单和黑名单
# ---------------------------------------------------------------------------

VNEXT_ALLOWED_TOOLS = frozenset({
    "read_dir",
    "read_file",
    "write_file",
    "list_skills",
    "load_skill",
    "complete",
})

VNEXT_FORBIDDEN_TOOLS = frozenset({
    "ask_user",
    "run_checks",
    "run_command",
    "decide_route",
    "write_plan",
    "complete_implementation",
    "submit_validation_report",
    "request_replan",
    "confirm_design",
    "select_skill",
    "choose_skill",
})


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_file_tools() -> MagicMock:
    """构造伪 FileTools，用于 build_vnext_tools 参数。"""
    return MagicMock()


def _make_skill_registry() -> MagicMock:
    """构造伪 skill_registry，用于 build_vnext_tools 参数。"""
    registry = MagicMock()
    registry.list_skills.return_value = []
    return registry


# ---------------------------------------------------------------------------
# 测试：vNext 工具白名单精确匹配
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _VNEXT_MODULES_AVAILABLE, reason="vNext 模块尚未实现 (Phase 2)")
class TestVNextToolsAllowOnlyMinimalSet:
    """验证 vNext 工具集合精确等于最小白名单。"""

    def test_vnext_tools_allow_only_minimal_set(self):
        """
        build_vnext_tools() 返回的工具名集合精确等于白名单。

        防止：后续 AI 顺手加入额外工具，扩大权限范围。
        """
        file_tools = _make_file_tools()
        skill_registry = _make_skill_registry()
        state = SingleImplementState()

        tools = build_vnext_tools(
            file_tools=file_tools,
            skill_registry=skill_registry,
            state=state,
        )
        names = {tool.name for tool in tools}

        assert names == VNEXT_ALLOWED_TOOLS, (
            f"vNext 工具集合必须精确等于白名单。"
            f"实际: {names}, 期望: {VNEXT_ALLOWED_TOOLS}"
        )

    def test_vnext_tools_count_is_six(self):
        """
        vNext 工具数量必须恰好为 6。

        防止：工具数量变化未被察觉。
        """
        file_tools = _make_file_tools()
        skill_registry = _make_skill_registry()
        state = SingleImplementState()

        tools = build_vnext_tools(
            file_tools=file_tools,
            skill_registry=skill_registry,
            state=state,
        )

        assert len(tools) == 6, (
            f"vNext 工具数量必须为 6，实际: {len(tools)}"
        )

    def test_vnext_tools_order_is_stable(self):
        """
        工具集合顺序固定：read_dir, read_file, write_file, list_skills, load_skill, complete。

        防止：工具顺序变化影响 Prompt 工具摘要和模型行为。
        """
        file_tools = _make_file_tools()
        skill_registry = _make_skill_registry()
        state = SingleImplementState()

        tools = build_vnext_tools(
            file_tools=file_tools,
            skill_registry=skill_registry,
            state=state,
        )
        names = [tool.name for tool in tools]

        expected_order = ["read_dir", "read_file", "write_file", "list_skills", "load_skill", "complete"]
        assert names == expected_order, (
            f"vNext 工具顺序必须固定。实际: {names}, 期望: {expected_order}"
        )


# ---------------------------------------------------------------------------
# 测试：vNext 工具排除禁止工具
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _VNEXT_MODULES_AVAILABLE, reason="vNext 模块尚未实现 (Phase 2)")
class TestVNextToolsExcludeForbiddenTools:
    """验证 vNext 工具集合不包含任何禁止工具。"""

    def test_vnext_tools_exclude_validation_and_plan_tools(self):
        """
        工具集合不包含任何 Plan / Validate / Route 相关工具。

        防止：旧工具混入 vNext，导致模型进入旧模式。
        """
        file_tools = _make_file_tools()
        skill_registry = _make_skill_registry()
        state = SingleImplementState()

        tools = build_vnext_tools(
            file_tools=file_tools,
            skill_registry=skill_registry,
            state=state,
        )
        names = {tool.name for tool in tools}

        for forbidden in VNEXT_FORBIDDEN_TOOLS:
            assert forbidden not in names, (
                f"vNext 工具集合禁止包含: {forbidden}"
            )

    @pytest.mark.parametrize("forbidden_tool", list(VNEXT_FORBIDDEN_TOOLS))
    def test_vnext_tools_exclude_each_forbidden_tool(self, forbidden_tool):
        """
        逐个验证每个禁止工具不存在于工具集合。

        防止：某个禁止工具被遗漏检查。
        """
        file_tools = _make_file_tools()
        skill_registry = _make_skill_registry()
        state = SingleImplementState()

        tools = build_vnext_tools(
            file_tools=file_tools,
            skill_registry=skill_registry,
            state=state,
        )
        names = {tool.name for tool in tools}

        assert forbidden_tool not in names, (
            f"vNext 工具集合禁止包含: {forbidden_tool}"
        )


# ---------------------------------------------------------------------------
# 测试：vNext 工具描述不引用旧模式
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _VNEXT_MODULES_AVAILABLE, reason="vNext 模块尚未实现 (Phase 2)")
class TestVNextToolDescriptionsDoNotReferenceModes:
    """验证 vNext 工具描述不提 Plan / Validate / Route 等旧模式。"""

    def test_vnext_tool_descriptions_do_not_reference_modes(self):
        """
        工具描述中不得出现校验、规划、路由、询问用户等旧模式语义。

        防止：工具描述暗示模型调用另一个阶段工具，导致模式混乱。
        """
        file_tools = _make_file_tools()
        skill_registry = _make_skill_registry()
        state = SingleImplementState()

        tools = build_vnext_tools(
            file_tools=file_tools,
            skill_registry=skill_registry,
            state=state,
        )

        forbidden_description_terms = [
            "校验",
            "规划",
            "路由",
            "询问用户",
            "Plan",
            "Validate",
            "Route",
            "ask_user",
            "run_checks",
            "decide_route",
            "write_plan",
            "submit_validation",
            "request_replan",
            "confirm_design",
        ]

        for tool in tools:
            description = tool.description or ""
            for term in forbidden_description_terms:
                assert term not in description, (
                    f"工具 {tool.name} 的描述不应包含旧模式语义: {term}"
                )

    def test_vnext_complete_tool_is_only_completion_exit(self):
        """
        complete 工具是 vNext 唯一完成出口，描述不得提及验证或构建。

        防止：complete 工具描述暗示完成后进入验证或构建流程。
        """
        file_tools = _make_file_tools()
        skill_registry = _make_skill_registry()
        state = SingleImplementState()

        tools = build_vnext_tools(
            file_tools=file_tools,
            skill_registry=skill_registry,
            state=state,
        )

        complete_tool = next(t for t in tools if t.name == "complete")
        description = complete_tool.description or ""

        assert "验证" not in description, (
            "complete 工具描述不应提及验证"
        )
        assert "构建" not in description, (
            "complete 工具描述不应提及构建"
        )
        assert "run_checks" not in description, (
            "complete 工具描述不应提及 run_checks"
        )

    def test_vnext_skill_tools_do_not_reference_old_skill_tools(self):
        """
        list_skills / load_skill 工具描述不得提及旧 select_skill / choose_skill。

        防止：工具描述暗示旧 Skill 选择流程。
        """
        file_tools = _make_file_tools()
        skill_registry = _make_skill_registry()
        state = SingleImplementState()

        tools = build_vnext_tools(
            file_tools=file_tools,
            skill_registry=skill_registry,
            state=state,
        )

        for tool in tools:
            if tool.name in ("list_skills", "load_skill"):
                description = tool.description or ""
                assert "select_skill" not in description, (
                    f"{tool.name} 描述不应提及旧 select_skill"
                )
                assert "choose_skill" not in description, (
                    f"{tool.name} 描述不应提及旧 choose_skill"
                )
