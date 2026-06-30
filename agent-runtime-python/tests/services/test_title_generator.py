from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.title_generator import TitleGeneratorService, normalize_title


def test_normalize_title_strips_prefix_and_quotes():
    assert normalize_title('标题："智能排班助手"\n这是解释', 12) == "智能排班助手"


@pytest.mark.asyncio
async def test_generate_app_title_returns_normalized_first_line():
    chat_model = MagicMock()
    chat_model.ainvoke = AsyncMock(return_value=MagicMock(content='标题：\n"智能排班助手"\n这是解释'))
    factory = MagicMock()
    factory.create.return_value = chat_model
    service = TitleGeneratorService(factory)

    title = await service.generate_app_title(
        "请帮我做一个排班系统",
        {
            "provider": "openai",
            "modelName": "light-model",
            "baseUrl": "https://example.com",
            "apiKey": "secret",
        },
    )

    assert title == "智能排班助手"
