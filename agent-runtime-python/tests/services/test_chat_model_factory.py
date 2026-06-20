import pytest

from app.core.exceptions import AgentRuntimeError
from app.services.chat_model_factory import ChatModelFactory


def test_create_openai_model_uses_runtime_config():
    config = {
        "provider": "openai",
        "modelName": "gpt-test",
        "baseUrl": "https://api.example.com/v1",
        "apiKey": "sk-test",
    }

    model = ChatModelFactory().create(config)

    assert model is not None
    assert model.model_name == "gpt-test"
    assert model.openai_api_base == "https://api.example.com/v1"


def test_create_openai_compatible_provider():
    config = {
        "provider": "openai-compatible",
        "modelName": "deepseek-chat",
        "baseUrl": "https://api.deepseek.com/v1",
        "apiKey": "sk-test",
    }

    model = ChatModelFactory().create(config)

    assert model is not None
    assert model.model_name == "deepseek-chat"


def test_create_rejects_unsupported_provider():
    config = {
        "provider": "anthropic",
        "modelName": "claude-3",
        "apiKey": "sk-test",
    }

    with pytest.raises(AgentRuntimeError, match="不支持的模型提供商"):
        ChatModelFactory().create(config)


def test_create_rejects_missing_api_key():
    config = {
        "provider": "openai",
        "modelName": "gpt-test",
        "baseUrl": "https://api.example.com/v1",
    }

    with pytest.raises(AgentRuntimeError, match="模型 API Key 不能为空"):
        ChatModelFactory().create(config)


def test_create_rejects_missing_model_name():
    config = {"provider": "openai", "apiKey": "sk-test"}

    with pytest.raises(AgentRuntimeError, match="模型名称不能为空"):
        ChatModelFactory().create(config)


def test_create_without_base_url():
    config = {
        "provider": "openai",
        "modelName": "gpt-4o",
        "apiKey": "sk-test",
    }

    model = ChatModelFactory().create(config)

    assert model is not None
    assert model.model_name == "gpt-4o"


def test_create_with_timeout():
    config = {
        "provider": "openai",
        "modelName": "gpt-test",
        "apiKey": "sk-test",
        "timeout": 60,
    }

    model = ChatModelFactory().create(config)

    assert model is not None
