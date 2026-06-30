import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent_loop_vnext.base.result import AgentResult
from app.runtime.context import RunMode
from app.runtime.events import RuntimeEvent, RuntimeEventType
from app.runtime.orchestrator import RuntimeOrchestrator
from app.runtime.services import RuntimeServices


def _make_request(**overrides) -> MagicMock:
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


async def _async_empty_gen(*_args, **_kwargs):
    if False:
        yield


class TestConductorVNextOrchestrator:
    @pytest.mark.asyncio
    async def test_run_conductor_vnext_uses_conductor_agent(self):
        orchestrator = RuntimeOrchestrator()
        request = _make_request()
        context = MagicMock()
        services = MagicMock()

        with (
            patch.object(orchestrator, "_build_context", new=AsyncMock(return_value=context)),
            patch.object(orchestrator, "_build_services", return_value=services),
            patch.object(orchestrator, "_drain_events", side_effect=_async_empty_gen),
            patch.object(orchestrator._platform_client, "complete_agent_run", new=AsyncMock(return_value=True)),
            patch("app.runtime.orchestrator.ConductorAgent") as mock_conductor_cls,
        ):
            mock_agent = mock_conductor_cls.return_value
            mock_agent.run = AsyncMock(return_value=AgentResult(status="completed", message="最终总结", agent_name="conductor"))

            events = []
            async for event in orchestrator._run_conductor_vnext(request, RunMode.GENERATE):
                events.append(event)

            mock_conductor_cls.assert_called_once()
            mock_agent.run.assert_awaited_once_with(context, services)

    @pytest.mark.asyncio
    async def test_run_conductor_vnext_persists_conductor_result(self):
        orchestrator = RuntimeOrchestrator()
        request = _make_request()
        context = MagicMock(is_test=False)
        services = MagicMock()

        with (
            patch.object(orchestrator, "_build_context", new=AsyncMock(return_value=context)),
            patch.object(orchestrator, "_build_services", return_value=services),
            patch.object(orchestrator, "_drain_events", side_effect=_async_empty_gen),
            patch.object(orchestrator._platform_client, "complete_agent_run", new=AsyncMock(return_value=True)) as mock_complete,
            patch("app.runtime.orchestrator.ConductorAgent") as mock_conductor_cls,
        ):
            mock_agent = mock_conductor_cls.return_value
            mock_agent.run = AsyncMock(return_value=AgentResult(
                status="completed",
                message="Conductor 最终总结",
                agent_name="conductor",
                artifacts={
                    "token_usage": [
                        {
                            "input_tokens": 11,
                            "output_tokens": 7,
                            "cache_read_tokens": 3,
                            "cache_creation_tokens": 1,
                        }
                    ]
                },
            ))

            async for _ in orchestrator._run_conductor_vnext(request, RunMode.GENERATE):
                pass

            mock_complete.assert_awaited_once()
            kwargs = mock_complete.await_args.kwargs
            assert kwargs["success"] is True
            assert kwargs["ai_message"] == "Conductor 最终总结"
            assert kwargs["ai_status"] == "success"
            assert kwargs["total_input_tokens"] == 11
            assert kwargs["total_output_tokens"] == 7
            assert kwargs["total_cache_read_tokens"] == 3
            assert kwargs["total_cache_creation_tokens"] == 1

    @pytest.mark.asyncio
    async def test_run_conductor_vnext_persists_tool_calls_in_ai_extra(self):
        orchestrator = RuntimeOrchestrator()
        request = _make_request()
        context = MagicMock(is_test=False)

        async def _run_with_tool_events(_context, runtime_services):
            await runtime_services.event_bus.emit(
                RuntimeEvent(
                    RuntimeEventType.TOOL_CALL,
                    {
                        "id": "call-1",
                        "name": "delegate_to_agent",
                        "arguments": {"agent_name": "implementor", "task": "实现登录页"},
                        "agent_name": "conductor",
                    },
                )
            )
            await runtime_services.event_bus.emit(
                RuntimeEvent(
                    RuntimeEventType.TOOL_RESULT,
                    {
                        "id": "call-1",
                        "name": "delegate_to_agent",
                        "arguments": {"agent_name": "implementor", "task": "实现登录页"},
                        "result": "实现完成",
                        "agent_name": "conductor",
                    },
                )
            )
            return AgentResult(status="completed", message="Conductor 最终总结", agent_name="conductor")

        with (
            patch.object(orchestrator, "_build_context", new=AsyncMock(return_value=context)),
            patch.object(orchestrator, "_drain_events", side_effect=_async_empty_gen),
            patch.object(orchestrator._platform_client, "complete_agent_run", new=AsyncMock(return_value=True)) as mock_complete,
            patch("app.runtime.orchestrator.ConductorAgent") as mock_conductor_cls,
        ):
            patcher = patch.object(
                orchestrator,
                "_build_services",
                side_effect=lambda event_bus: RuntimeServices(event_bus=event_bus),
            )
            with patcher:
                mock_agent = mock_conductor_cls.return_value
                mock_agent.run = AsyncMock(side_effect=_run_with_tool_events)

                async for _ in orchestrator._run_conductor_vnext(request, RunMode.GENERATE):
                    pass

                kwargs = mock_complete.await_args.kwargs
                parsed_extra = json.loads(kwargs["ai_extra"])
                assert parsed_extra["toolCalls"][0]["name"] == "delegate_to_agent"
                assert parsed_extra["toolCalls"][0]["agentName"] == "conductor"
                assert parsed_extra["toolCalls"][1]["type"] == "executed"
