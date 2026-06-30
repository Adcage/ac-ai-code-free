import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.runtime.orchestrator import RuntimeOrchestrator
from app.runtime.context import RunMode


class TestRuntimeOrchestrator:
    @pytest.mark.asyncio
    async def test_build_context_marks_resume_without_mutating_platform_history(self):
        orchestrator = RuntimeOrchestrator()
        prompt = "需求补充：企业后台登录页面\n\n请继续生成。"
        request = MagicMock(
            agent_run_id="42",
            app_id=0,
            session_id=9,
            user_id=7,
            prompt=prompt,
            code_gen_type=3,
            workspace_path="C:/tmp/workspace",
            original_content="",
            is_test=False,
        )
        history = [
            {"id": 1, "role": "user", "content": "创建登录页面"},
            {"id": 2, "role": "ai", "content": "您想创建什么样的登录界面？"},
            {"id": 3, "role": "user", "content": prompt},
        ]

        with patch.object(
            orchestrator._platform_client,
            "get_chat_history",
            new_callable=AsyncMock,
            return_value=history,
        ):
            context = await orchestrator._build_context(
                request,
                RunMode.GENERATE,
                is_resume=True,
            )

        assert context.is_resume is True
        assert context.prompt == prompt
        assert context.chat_history[-1].content == prompt

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Agent Loop requires real model; full integration test in E2E")
    async def test_stream_generate_yields_events(self):
        orchestrator = RuntimeOrchestrator()
        mock_request = MagicMock()
        mock_request.agent_run_id = "42"
        mock_request.app_id = 1
        mock_request.session_id = 1
        mock_request.user_id = 1
        mock_request.prompt = "生成一个简单的 HTML 页面"
        mock_request.code_gen_type = 1
        mock_request.workspace_path = "/tmp/test_workspace"

        with (
            patch.object(
                orchestrator._platform_client, "get_app_detail", new_callable=AsyncMock
            ) as mock_app,
            patch.object(
                orchestrator._platform_client,
                "get_chat_history",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch.object(
                orchestrator._platform_client,
                "resolve_runtime_model_bundle",
                new_callable=AsyncMock,
            ) as mock_bundle,
            patch.object(
                orchestrator._chat_model_factory, "create", new_callable=AsyncMock
            ) as mock_create,
        ):
            mock_app.return_value = {
                "id": 1,
                "name": "test",
                "description": "",
                "codeGenType": 3,
                "userId": 1,
            }
            from app.modeling.resolver import ResolvedModelConfig
            from app.modeling.roles import ModelRole

            mock_bundle.return_value = {
                ModelRole.PRIMARY: ResolvedModelConfig(
                    role=ModelRole.PRIMARY,
                    provider="openai",
                    model_name="gpt-4o-mini",
                    base_url="https://api.openai.com/v1",
                    api_key="test-key",
                ),
            }
            mock_llm = AsyncMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_response = MagicMock()
            mock_response.content = "这是一个简单的页面"
            mock_response.tool_calls = []
            mock_llm.ainvoke.return_value = mock_response
            mock_create.return_value = mock_llm

            events = []
            async for event in orchestrator.stream_generate(mock_request):
                events.append(event)

            event_types = [e.event_type for e in events]
            assert any(t for t in event_types), "Should yield at least one proto event"
