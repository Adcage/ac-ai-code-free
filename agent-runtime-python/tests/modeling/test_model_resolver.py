import pytest
from unittest.mock import AsyncMock

from app.modeling.policy import ModelPolicy, ModelRole
from app.modeling.resolver import ModelResolver, ResolvedModelConfig
from app.runtime.context import CodeGenType, ExecutionContext, RunMode


def _make_context(**overrides) -> ExecutionContext:
    defaults = dict(
        agent_run_id=1,
        app_id=1,
        session_id=1,
        user_id=1,
        prompt="test",
        code_gen_type=CodeGenType.VUE_PROJECT,
        workspace_path="/tmp",
        run_mode=RunMode.GENERATE,
    )
    defaults.update(overrides)
    return ExecutionContext(**defaults)


class TestModelPolicy:
    def test_role_for_known_node(self):
        policy = ModelPolicy()
        assert policy.role_for_node("call_model") == ModelRole.PRIMARY
        assert policy.role_for_node("classify_task") == ModelRole.LIGHT

    def test_role_for_unknown_node_defaults_to_primary(self):
        policy = ModelPolicy()
        assert policy.role_for_node("unknown_node") == ModelRole.PRIMARY


class TestModelResolver:
    @pytest.mark.asyncio
    async def test_load_bundle_success(self):
        mock_client = AsyncMock()
        bundle = {
            ModelRole.LIGHT: ResolvedModelConfig(
                role=ModelRole.LIGHT,
                provider="openai",
                model_name="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                api_key="key1",
                source="SYSTEM",
                billing_mode="SYSTEM_FREE_FALLBACK",
            ),
            ModelRole.PRIMARY: ResolvedModelConfig(
                role=ModelRole.PRIMARY,
                provider="openai",
                model_name="gpt-4o",
                base_url="https://api.openai.com/v1",
                api_key="key1",
                source="SYSTEM",
                billing_mode="SYSTEM_FREE_FALLBACK",
            ),
        }
        mock_client.resolve_runtime_model_bundle.return_value = bundle

        resolver = ModelResolver(mock_client)
        ctx = _make_context()
        await resolver.load_bundle(ctx)

        result = resolver.resolve(ModelRole.PRIMARY)
        assert result.model_name == "gpt-4o"
        assert result.source == "SYSTEM"

    @pytest.mark.asyncio
    async def test_resolve_falls_back_to_primary(self):
        mock_client = AsyncMock()
        bundle = {
            ModelRole.PRIMARY: ResolvedModelConfig(
                role=ModelRole.PRIMARY,
                provider="openai",
                model_name="gpt-4o",
                base_url="https://api.openai.com/v1",
                api_key="key1",
            ),
        }
        mock_client.resolve_runtime_model_bundle.return_value = bundle

        resolver = ModelResolver(mock_client)
        ctx = _make_context()
        await resolver.load_bundle(ctx)

        result = resolver.resolve(ModelRole.LIGHT)
        assert result.model_name == "gpt-4o"

    @pytest.mark.asyncio
    async def test_resolve_raises_when_empty(self):
        mock_client = AsyncMock()
        mock_client.resolve_runtime_model_bundle.side_effect = RuntimeError("no bundle")

        resolver = ModelResolver(mock_client)
        ctx = _make_context()

        with pytest.raises(Exception):
            await resolver.load_bundle(ctx)
