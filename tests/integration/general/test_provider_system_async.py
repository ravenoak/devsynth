import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from devsynth.adapters.provider_system import (
    OpenAIProvider,
    FallbackProvider,
    acomplete,
    aembed,
    ProviderError,
)


@pytest.mark.asyncio
@pytest.mark.medium
async def test_openai_provider_acomplete():
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "Async"}}]}
    mock_response.raise_for_status.return_value = None

    async_client = AsyncMock()
    async_client.__aenter__.return_value = async_client
    async_client.__aexit__.return_value = None
    async_client.post.return_value = mock_response

    with patch("devsynth.adapters.provider_system.httpx.AsyncClient", return_value=async_client):
        provider = OpenAIProvider(api_key="key")
        result = await provider.acomplete("test prompt")
        assert result == "Async"
        async_client.post.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.medium
async def test_acomplete_function():
    mock_provider = AsyncMock()
    mock_provider.acomplete.return_value = "response"
    with patch("devsynth.adapters.provider_system.get_provider", return_value=mock_provider):
        result = await acomplete("prompt")
        assert result == "response"
        mock_provider.acomplete.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.medium
async def test_aembed_function():
    mock_provider = AsyncMock()
    mock_provider.aembed.return_value = [[0.1, 0.2]]
    with patch("devsynth.adapters.provider_system.get_provider", return_value=mock_provider):
        result = await aembed("text")
        assert result == [[0.1, 0.2]]
        mock_provider.aembed.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.medium
async def test_fallback_provider_acomplete():
    provider1 = AsyncMock()
    provider1.acomplete.side_effect = ProviderError("fail1")
    provider2 = AsyncMock()
    provider2.acomplete.return_value = "ok"
    fb = FallbackProvider(providers=[provider1, provider2])
    result = await fb.acomplete("hello")
    assert result == "ok"
    provider1.acomplete.assert_called_once()
    provider2.acomplete.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.medium
async def test_fallback_provider_aembed():
    provider1 = AsyncMock()
    provider1.aembed.side_effect = ProviderError("fail1")
    provider2 = AsyncMock()
    provider2.aembed.return_value = [[1.0]]
    fb = FallbackProvider(providers=[provider1, provider2])
    result = await fb.aembed("hi")
    assert result == [[1.0]]
    provider1.aembed.assert_called_once()
    provider2.aembed.assert_called_once()
