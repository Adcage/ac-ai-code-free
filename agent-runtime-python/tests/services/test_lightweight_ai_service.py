from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modeling.resolver import ResolvedModelConfig
from app.modeling.roles import ModelRole
from app.services.lightweight_ai_service import LightweightAiService


def _resolved(role: ModelRole, model_name: str) -> ResolvedModelConfig:
    return ResolvedModelConfig(
        role=role,
        provider="openai",
        model_name=model_name,
        base_url="https://example.com",
        api_key="secret",
        source="runtime",
        billing_mode="shared",
    )


@pytest.mark.asyncio
async def test_enhance_prompt_prefers_light_model():
    platform_client = AsyncMock()
    platform_client.resolve_runtime_model_bundle.return_value = {
        ModelRole.PRIMARY: _resolved(ModelRole.PRIMARY, "primary-model"),
        ModelRole.LIGHT: _resolved(ModelRole.LIGHT, "light-model"),
    }
    prompt_enhancer = MagicMock()
    prompt_enhancer.enhance = AsyncMock(return_value="enhanced")

    service = LightweightAiService(
        platform_client=platform_client,
        prompt_enhancer=prompt_enhancer,
        title_generator=MagicMock(),
    )

    result = await service.enhance_prompt("请做一个登录页")

    assert result == "enhanced"
    model_config = prompt_enhancer.enhance.await_args.args[1]
    assert model_config["modelName"] == "light-model"


@pytest.mark.asyncio
async def test_generate_app_title_falls_back_to_primary_model():
    platform_client = AsyncMock()
    platform_client.resolve_runtime_model_bundle.return_value = {
        ModelRole.PRIMARY: _resolved(ModelRole.PRIMARY, "primary-model"),
    }
    title_generator = MagicMock()
    title_generator.generate_app_title = AsyncMock(return_value="智能排班助手")

    service = LightweightAiService(
        platform_client=platform_client,
        prompt_enhancer=MagicMock(),
        title_generator=title_generator,
    )

    result = await service.generate_app_title("请帮我做一个排班系统")

    assert result == "智能排班助手"
    model_config = title_generator.generate_app_title.await_args.args[1]
    assert model_config["modelName"] == "primary-model"
