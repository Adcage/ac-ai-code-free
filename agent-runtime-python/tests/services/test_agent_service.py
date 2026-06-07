from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.schemas.code_generation import CodeGenerationRequest
from app.services.agent_service import AgentService
from app.services.chat_model_factory import ChatModelFactory
from app.services.model_config_client import ModelConfigClient
from app.services.prompt_builder import PromptBuilder


class FakeChatModel:
    async def ainvoke(self, messages):
        return AIMessage(content="<template><main><h1>Portfolio</h1></main></template>")


class FakeChatModelFactory(ChatModelFactory):
    def __init__(self, fake_model: FakeChatModel):
        self._fake_model = fake_model

    def create(self, config: dict):
        return self._fake_model


@pytest.mark.asyncio
async def test_agent_service_with_model_config(tmp_path: Path):
    fake_model = FakeChatModel()
    model_config_client = AsyncMock(spec=ModelConfigClient)
    model_config_client.get_runtime_config.return_value = {
        "provider": "openai",
        "modelName": "gpt-4",
        "apiKey": "test-key",
        "baseUrl": "",
    }
    chat_model_factory = FakeChatModelFactory(fake_model)
    prompt_builder = PromptBuilder()

    service = AgentService(model_config_client, chat_model_factory, prompt_builder)
    request = CodeGenerationRequest(
        agentRunId="1",
        appId=2,
        sessionId=3,
        userId=4,
        prompt="创建一个首页",
        codeGenType="vue_project",
        workspacePath=str(tmp_path),
        modelConfigId=10,
        configVersion=1,
    )

    events = [event async for event in service.stream(request)]
    event_types = [event.eventType for event in events]

    assert "agent_start" in event_types
    assert "ai_response" in event_types
    assert "tool_request" in event_types
    assert "tool_executed" in event_types
    assert "done" in event_types
    assert (tmp_path / "src" / "App.vue").exists()
    content = (tmp_path / "src" / "App.vue").read_text(encoding="utf-8")
    assert "Portfolio" in content

    ai_response_idx = event_types.index("ai_response")
    tool_request_idx = event_types.index("tool_request")
    assert ai_response_idx < tool_request_idx


@pytest.mark.asyncio
async def test_agent_service_model_config_integration(tmp_path: Path):
    fake_model = FakeChatModel()
    model_config_client = AsyncMock(spec=ModelConfigClient)
    fake_config = {
        "provider": "openai-compatible",
        "modelName": "fake-model",
        "apiKey": "fake-key",
        "baseUrl": "https://fake.api.com/v1",
    }
    model_config_client.get_runtime_config.return_value = fake_config
    chat_model_factory = FakeChatModelFactory(fake_model)
    create_spy = MagicMock(wraps=chat_model_factory.create)
    chat_model_factory.create = create_spy
    prompt_builder = PromptBuilder()

    service = AgentService(model_config_client, chat_model_factory, prompt_builder)
    request = CodeGenerationRequest(
        agentRunId="10",
        appId=20,
        sessionId=30,
        userId=40,
        prompt="创建一个首页",
        codeGenType="vue_project",
        workspacePath=str(tmp_path),
        modelConfigId=99,
        configVersion=2,
    )

    events = [event async for event in service.stream(request)]

    model_config_client.get_runtime_config.assert_awaited_once_with(99, 2)
    create_spy.assert_called_once_with(fake_config)
    assert (tmp_path / "src" / "App.vue").exists()
    content = (tmp_path / "src" / "App.vue").read_text(encoding="utf-8")
    assert "Portfolio" in content


@pytest.mark.asyncio
async def test_agent_service_without_model_config(tmp_path: Path):
    model_config_client = AsyncMock(spec=ModelConfigClient)
    chat_model_factory = ChatModelFactory()
    prompt_builder = PromptBuilder()

    service = AgentService(model_config_client, chat_model_factory, prompt_builder)
    request = CodeGenerationRequest(
        agentRunId="2",
        appId=3,
        sessionId=4,
        userId=5,
        prompt="创建一个首页",
        codeGenType="vue_project",
        workspacePath=str(tmp_path),
    )

    events = [event async for event in service.stream(request)]
    event_types = [event.eventType for event in events]

    assert "agent_start" in event_types
    assert "ai_response" in event_types
    assert "tool_request" in event_types
    assert "tool_executed" in event_types
    assert "done" in event_types
    assert (tmp_path / "src" / "App.vue").exists()
