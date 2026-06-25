"""
Phase 0 Task 0-1: vNext 上下文边界失败测试

本测试文件锁定 vNext Context Engine 的最小输入边界：
- 只允许当前用户需求、工作区摘要、已加载 Skill、已写文件列表、最近工具观察摘要进入 LLM 输入
- 禁止旧 chat history、旧 tool history、conversation messages、resume 文本进入

当前阶段：这些测试引用的模块尚不存在，预期因 ImportError 失败。
后续 Phase 1 实现后，这些测试必须通过。
"""

import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# 导入未来 vNext 模块 — Phase 0 阶段这些导入会失败，这是预期行为
# ---------------------------------------------------------------------------

try:
    from app.agent_loop_vnext.context_engine import (
        VNextContextEngine,
        VNextContextSnapshot,
    )
    from app.agent_loop_vnext.state import SingleImplementState

    _VNEXT_MODULES_AVAILABLE = True
except ImportError:
    _VNEXT_MODULES_AVAILABLE = False


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_legacy_context(**overrides) -> SimpleNamespace:
    """
    构造一个带有旧上下文污染源的伪 context。

    模拟 ExecutionContext 中可能存在的旧字段，
    用于验证 VNextContextEngine 不会读取这些字段。
    """
    defaults = dict(
        prompt="请生成登录页",
        agent_run_id=1,
        app_id=1,
        session_id=1,
        user_id=1,
        workspace_path="/workspace/test",
        # 旧上下文污染源 — vNext 不应读取
        chat_history=[
            SimpleNamespace(id=1, role="user", content="之前的历史消息1"),
            SimpleNamespace(id=2, role="assistant", content="之前的历史回复1"),
        ],
        original_content="旧文件内容",
        is_resume=True,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_vnext_state(**overrides) -> dict:
    """
    构造 vNext state 的预期字段字典。

    Phase 0 阶段无法实例化 SingleImplementState，
    使用字典描述预期结构。
    """
    defaults = dict(
        status="running",
        iteration=0,
        max_iterations=12,
        written_files=[],
        read_files=[],
        loaded_skill=None,
        observations=[],
        final_summary="",
        error_message="",
    )
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# 测试：vNext 上下文排除旧聊天历史
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _VNEXT_MODULES_AVAILABLE, reason="vNext 模块尚未实现 (Phase 1)")
class TestVNextContextExcludesChatHistory:
    """验证 VNextContextEngine 不注入旧聊天历史到 LLM messages。"""

    def test_vnext_context_excludes_chat_history(self):
        """
        输入含 chat_history 的 context，输出 messages 不含历史内容。

        防止：旧聊天历史污染 vNext 干净上下文，导致模型重复历史行为。
        """
        context = _make_legacy_context()
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        # 提取所有消息文本内容
        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        # 断言：不包含旧聊天历史内容
        assert "之前的历史消息1" not in all_text, (
            "vNext 上下文不应包含旧聊天历史内容"
        )
        assert "之前的历史回复1" not in all_text, (
            "vNext 上下文不应包含旧聊天历史内容"
        )

    def test_vnext_context_excludes_legacy_tool_history(self):
        """
        输入含旧工具历史的 context，输出 messages 不含"历史工具操作记录"。

        防止：旧 tool_history 对模型形成强暗示，诱发重复 write_file 或 run_checks。
        """
        context = _make_legacy_context()
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        # 断言：不包含旧工具历史关键词
        forbidden_terms = [
            "历史工具操作记录",
            "executed_tool_calls",
            "ToolCallRecord",
            "tool_history",
        ]
        for term in forbidden_terms:
            assert term not in all_text, (
                f"vNext 上下文不应包含旧工具历史关键词: {term}"
            )

    def test_vnext_context_excludes_conversation_messages(self):
        """
        输出 messages 不包含旧 conversation_messages。

        防止：旧 conversation_messages 可能包含跨阶段累积的上下文，
        是旧链路重复行为的根因之一。
        """
        context = _make_legacy_context()
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        assert "conversation_messages" not in all_text, (
            "vNext 上下文不应包含旧 conversation_messages"
        )

    def test_vnext_context_excludes_resume_text(self):
        """
        输出 messages 不包含 <<RESUME_ANSWERS>> 或 resume 相关文本。

        防止：vNext 第一版不支持 resume，不应注入旧 resume 文本。
        """
        context = _make_legacy_context(is_resume=True)
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        assert "<<RESUME_ANSWERS>>" not in all_text, (
            "vNext 上下文不应包含旧 resume 文本标记"
        )
        assert "resume" not in all_text.lower() or "不支持 resume" in all_text, (
            "vNext 上下文不应包含 resume 语义（除非是明确说明不支持）"
        )


# ---------------------------------------------------------------------------
# 测试：vNext 上下文只包含当前 prompt 和 vNext state 摘要
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _VNEXT_MODULES_AVAILABLE, reason="vNext 模块尚未实现 (Phase 1)")
class TestVNextContextContainsOnlyCurrentPromptAndState:
    """验证 VNextContextEngine 输出只包含当前 prompt 和 vNext state 摘要。"""

    def test_vnext_context_contains_current_prompt(self):
        """
        输出 messages 必须包含当前用户需求。

        防止：vNext 丢失用户实际需求。
        """
        context = _make_legacy_context(prompt="请生成一个登录页面")
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        assert "请生成一个登录页面" in all_text, (
            "vNext 上下文必须包含当前用户需求"
        )

    def test_vnext_context_contains_written_files(self):
        """
        输出 messages 包含 vNext state 的 written_files。

        防止：模型不知道已写过哪些文件，导致重复写入。
        """
        context = _make_legacy_context()
        state = SingleImplementState()
        state.written_files = ["src/Login.vue", "src/api/login.ts"]

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        assert "src/Login.vue" in all_text, (
            "vNext 上下文应包含已写文件列表"
        )

    def test_vnext_context_contains_loaded_skill_summary(self):
        """
        输出 messages 包含已加载 Skill 的摘要。

        防止：模型不知道已加载 Skill，重复加载或忽略 Skill 规则。
        """
        context = _make_legacy_context()
        state = SingleImplementState()
        # 模拟已加载 Skill（Phase 1 实现后使用 LoadedSkill dataclass）
        state.loaded_skill = SimpleNamespace(
            skill_id="vue3-dashboard",
            name="Vue3 Dashboard",
            description="Vue3 仪表盘 Skill",
            body="## 规则\n使用 Composition API",
            source_path="skills/vue3-dashboard.md",
            references=[],
        )

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        assert "Vue3 Dashboard" in all_text, (
            "vNext 上下文应包含已加载 Skill 摘要"
        )

    def test_vnext_context_contains_observations(self):
        """
        输出 messages 包含 vNext state 的 observations 摘要。

        防止：模型丢失最近工具执行结果的上下文。
        """
        context = _make_legacy_context()
        state = SingleImplementState()
        # 模拟 observations（Phase 1 实现后使用 VNextObservation dataclass）
        state.observations = [
            SimpleNamespace(
                kind="tool_result",
                source="read_dir",
                summary="目录包含 3 个文件",
                data={},
            )
        ]

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        assert "目录包含 3 个文件" in all_text, (
            "vNext 上下文应包含 observations 摘要"
        )


# ---------------------------------------------------------------------------
# 测试：vNext Prompt 不含旧模式词
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _VNEXT_MODULES_AVAILABLE, reason="vNext 模块尚未实现 (Phase 1)")
class TestVNextPromptExcludesLegacyModes:
    """验证 vNext Prompt 不含 Plan / Route / Validate / 旧工具等语义。"""

    def test_vnext_prompt_excludes_plan_mode(self):
        """System prompt 不包含 Plan Mode 语义。"""
        context = _make_legacy_context()
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        system_text = ""
        for msg in messages:
            if hasattr(msg, "type") and msg.type == "system":
                system_text += msg.content

        assert "Plan Mode" not in system_text, (
            "vNext System Prompt 不应包含 Plan Mode 语义"
        )
        assert "规划模式" not in system_text, (
            "vNext System Prompt 不应包含规划模式语义"
        )

    def test_vnext_prompt_excludes_route(self):
        """System prompt 不包含 Route 语义。"""
        context = _make_legacy_context()
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        system_text = ""
        for msg in messages:
            if hasattr(msg, "type") and msg.type == "system":
                system_text += msg.content

        assert "Route" not in system_text, (
            "vNext System Prompt 不应包含 Route 语义"
        )
        assert "路由" not in system_text, (
            "vNext System Prompt 不应包含路由语义"
        )

    def test_vnext_prompt_excludes_validate(self):
        """System prompt 不包含 Validate / 校验 语义。"""
        context = _make_legacy_context()
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        system_text = ""
        for msg in messages:
            if hasattr(msg, "type") and msg.type == "system":
                system_text += msg.content

        assert "Validate" not in system_text, (
            "vNext System Prompt 不应包含 Validate 语义"
        )
        assert "校验模式" not in system_text, (
            "vNext System Prompt 不应包含校验模式语义"
        )

    def test_vnext_prompt_excludes_disallowed_tools(self):
        """System prompt 不包含 run_checks / ask_user 等禁止工具。"""
        context = _make_legacy_context()
        state = SingleImplementState()

        engine = VNextContextEngine()
        messages = engine.build_messages(context, state)

        all_text = " ".join(
            msg.content for msg in messages if hasattr(msg, "content")
        )

        forbidden_tool_terms = [
            "run_checks",
            "ask_user",
            "历史工具操作记录",
        ]
        for term in forbidden_tool_terms:
            assert term not in all_text, (
                f"vNext Prompt 不应包含禁止工具引用: {term}"
            )
