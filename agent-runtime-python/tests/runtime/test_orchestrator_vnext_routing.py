"""
Phase 0 Task 0-3: RuntimeOrchestrator vNext 分流目标测试

本测试文件锁定 /app/chat/gen/code/stream 默认走 vNext 的目标行为，
同时保留旧链路可被配置项显式选择的可能。

预期配置：
- settings.agent_loop_engine: str = "vnext"
- 合法值: vnext, legacy
- 非法值: 抛 AgentRuntimeError(code=STATE_ERROR)

当前阶段：这些测试引用的模块和配置尚不存在，预期因 ImportError/AttributeError 失败。
后续 Phase 3 实现后，这些测试必须通过。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 导入未来 vNext 模块和配置 — Phase 0 阶段这些导入可能失败
# ---------------------------------------------------------------------------

try:
    from app.agent_loop_vnext.runner import SingleImplementLoopRunner
    from app.core.config import Settings

    _VNEXT_MODULES_AVAILABLE = True
except ImportError:
    _VNEXT_MODULES_AVAILABLE = False

# 独立检查 Settings 是否有 agent_loop_engine 字段
_settings_has_engine = False
if _VNEXT_MODULES_AVAILABLE:
    try:
        _test_settings = Settings()
        _settings_has_engine = hasattr(_test_settings, "agent_loop_engine")
    except Exception:
        pass

try:
    from app.core.exceptions import AgentRuntimeError
    from app.core.error_codes import AgentErrorCode
except ImportError:
    AgentRuntimeError = None
    AgentErrorCode = None

from app.runtime.orchestrator import RuntimeOrchestrator
from app.runtime.context import RunMode


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_request(**overrides) -> MagicMock:
    """构造伪 gRPC 请求对象。"""
    defaults = dict(
        agent_run_id="42",
        app_id=1,
        session_id=1,
        user_id=1,
        prompt="生成一个登录页面",
        code_gen_type=3,
        workspace_path="/tmp/test_workspace",
        loop_state_json="",
        is_test=False,
        generation_mode=None,
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


# ---------------------------------------------------------------------------
# 测试：StreamGenerate 默认走 vNext
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _VNEXT_MODULES_AVAILABLE or not _settings_has_engine,
    reason="vNext 模块或 agent_loop_engine 配置尚未实现 (Phase 3)",
)
class TestStreamGenerateDefaultsToVNext:
    """验证 stream_generate() 默认调用 vNext runner。"""

    @pytest.mark.asyncio
    async def test_stream_generate_defaults_to_vnext(self):
        """
        默认配置 (agent_loop_engine="vnext") 下，
        stream_generate() 应调用 vNext runner 而非旧 _run_agent_loop。

        防止：默认仍走旧链路，vNext 替换未生效。
        """
        orchestrator = RuntimeOrchestrator()
        request = _make_request()

        # Mock 旧链路，确保不被调用
        with (
            patch.object(
                orchestrator,
                "_run_agent_loop",
                new_callable=AsyncMock,
            ) as mock_legacy,
            patch.object(
                orchestrator,
                "_run_single_implement_vnext",
            ) as mock_vnext,
            patch(
                "app.runtime.orchestrator.settings",
                agent_loop_engine="vnext",
            ),
        ):
            mock_vnext.side_effect = _async_empty_gen

            # 消费生成器
            events = []
            async for event in orchestrator.stream_generate(request):
                events.append(event)

            # 断言：调用了 vNext runner
            mock_vnext.assert_called_once()
            # 断言：未调用旧链路
            mock_legacy.assert_not_called()


# ---------------------------------------------------------------------------
# 测试：legacy 配置可显式回退
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _VNEXT_MODULES_AVAILABLE or not _settings_has_engine,
    reason="vNext 模块或 agent_loop_engine 配置尚未实现 (Phase 3)",
)
class TestStreamGenerateCanUseLegacyWhenConfigured:
    """验证 agent_loop_engine=legacy 时调用旧链路。"""

    @pytest.mark.asyncio
    async def test_stream_generate_can_use_legacy_when_configured(self):
        """
        agent_loop_engine="legacy" 时，stream_generate() 应调用旧 _run_agent_loop。

        防止：legacy 回退不可用，无法在 vNext 出问题时降级。
        """
        orchestrator = RuntimeOrchestrator()
        request = _make_request()

        with (
            patch.object(
                orchestrator,
                "_run_agent_loop",
            ) as mock_legacy,
            patch.object(
                orchestrator,
                "_run_single_implement_vnext",
                new_callable=AsyncMock,
            ) as mock_vnext,
            patch(
                "app.runtime.orchestrator.settings",
                agent_loop_engine="legacy",
            ),
        ):
            mock_legacy.side_effect = _async_empty_gen

            events = []
            async for event in orchestrator.stream_generate(request):
                events.append(event)

            # 断言：调用了旧链路
            mock_legacy.assert_called_once()
            # 断言：未调用 vNext runner
            mock_vnext.assert_not_called()


# ---------------------------------------------------------------------------
# 测试：非法配置抛 STATE_ERROR
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _VNEXT_MODULES_AVAILABLE or not _settings_has_engine,
    reason="vNext 模块或 agent_loop_engine 配置尚未实现 (Phase 3)",
)
class TestInvalidAgentLoopEngineRaisesStateError:
    """验证非法 agent_loop_engine 配置抛出 STATE_ERROR。"""

    @pytest.mark.asyncio
    async def test_invalid_agent_loop_engine_raises_state_error(self):
        """
        agent_loop_engine 为非法值时，stream_generate() 应抛出
        AgentRuntimeError(code=STATE_ERROR)。

        防止：非法配置静默回退到某个默认链路，导致行为不可预测。
        """
        orchestrator = RuntimeOrchestrator()
        request = _make_request()

        with patch(
            "app.runtime.orchestrator.settings",
            agent_loop_engine="invalid_engine",
        ):
            with pytest.raises(AgentRuntimeError) as exc_info:
                async for _ in orchestrator.stream_generate(request):
                    pass

            # 断言：错误码为 STATE_ERROR
            assert exc_info.value.code == AgentErrorCode.STATE_ERROR, (
                f"非法 agent_loop_engine 应抛 STATE_ERROR，"
                f"实际错误码: {exc_info.value.code}"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_value", ["unknown", "default", "auto", "", "VNEXT"])
    async def test_various_invalid_engine_values(self, invalid_value):
        """
        各种非法字符串都应抛 STATE_ERROR。

        防止：某些非法值被误认为合法。
        """
        orchestrator = RuntimeOrchestrator()
        request = _make_request()

        with patch(
            "app.runtime.orchestrator.settings",
            agent_loop_engine=invalid_value,
        ):
            with pytest.raises(AgentRuntimeError) as exc_info:
                async for _ in orchestrator.stream_generate(request):
                    pass

            assert exc_info.value.code == AgentErrorCode.STATE_ERROR


# ---------------------------------------------------------------------------
# 测试：agent_loop_engine 配置字段契约
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _VNEXT_MODULES_AVAILABLE,
    reason="vNext 模块尚未实现 (Phase 3)",
)
class TestAgentLoopEngineConfigContract:
    """验证 agent_loop_engine 配置字段的存在和默认值。"""

    def test_settings_has_agent_loop_engine_field(self):
        """
        Settings 类必须有 agent_loop_engine 字段。

        防止：配置字段遗漏，导致分流逻辑无法实现。
        """
        settings = Settings()
        assert hasattr(settings, "agent_loop_engine"), (
            "Settings 必须包含 agent_loop_engine 字段"
        )

    def test_agent_loop_engine_default_is_vnext(self):
        """
        agent_loop_engine 默认值必须为 "vnext"。

        防止：默认值为 "legacy"，导致 vNext 替换未生效。
        """
        settings = Settings()
        assert settings.agent_loop_engine == "vnext", (
            f"agent_loop_engine 默认值必须为 'vnext'，"
            f"实际: {settings.agent_loop_engine}"
        )


# ---------------------------------------------------------------------------
# 辅助：异步迭代器
# ---------------------------------------------------------------------------

async def _async_empty_gen(*args, **kwargs):
    """返回空异步生成器的辅助函数。"""
    if False:
        yield
