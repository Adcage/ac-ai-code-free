import httpx
import pytest

from app.services.model_config_client import ModelConfigClient


@pytest.mark.asyncio
async def test_get_runtime_config_returns_data():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Internal-Secret"] == "secret"
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "provider": "openai",
                    "modelName": "gpt-test",
                    "baseUrl": "http://model.example",
                    "apiKeyCipher": "cipher",
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://java") as http_client:
        client = ModelConfigClient("http://java", "secret", http_client=http_client)
        result = await client.get_runtime_config(1, 2)

    assert result["provider"] == "openai"
    assert result["modelName"] == "gpt-test"
