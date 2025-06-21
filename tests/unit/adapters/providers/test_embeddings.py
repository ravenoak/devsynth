import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from devsynth.adapters.provider_system import (
    OpenAIProvider,
    LMStudioProvider,
    embed,
    aembed,
    ProviderError,
)


def test_openai_provider_embed_calls_api():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"embedding": [0.1, 0.2]}]}
    mock_response.raise_for_status.return_value = None
    with patch(
        "devsynth.adapters.provider_system.requests.post", return_value=mock_response
    ) as mock_post:
        provider = OpenAIProvider(api_key="key")
        result = provider.embed("hello")
        assert result == [[0.1, 0.2]]
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_openai_provider_aembed_calls_api():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"embedding": [0.3, 0.4]}]}
    mock_response.raise_for_status.return_value = None
    async_client = AsyncMock()
    async_client.__aenter__.return_value = async_client
    async_client.__aexit__.return_value = None
    async_client.post.return_value = mock_response
    with patch(
        "devsynth.adapters.provider_system.httpx.AsyncClient", return_value=async_client
    ):
        provider = OpenAIProvider(api_key="key")
        result = await provider.aembed("world")
        assert result == [[0.3, 0.4]]
        async_client.post.assert_called_once()


def test_lmstudio_provider_embed_not_supported():
    provider = LMStudioProvider(endpoint="http://localhost:1234")
    with pytest.raises(ProviderError):
        provider.embed("text")


def test_embed_function_unsupported_provider():
    provider = LMStudioProvider(endpoint="http://localhost:1234")
    with patch("devsynth.adapters.provider_system.get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            embed("text", provider_type="lm_studio", fallback=False)


@pytest.mark.asyncio
async def test_aembed_function_unsupported_provider():
    provider = LMStudioProvider(endpoint="http://localhost:1234")
    with patch("devsynth.adapters.provider_system.get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            await aembed("text", provider_type="lm_studio", fallback=False)
