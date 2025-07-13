from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
import requests
from devsynth.adapters.provider_system import (
    LMStudioProvider,
    OpenAIProvider,
    ProviderError,
    aembed,
    embed,
)


def test_openai_provider_embed_calls_api_succeeds():
    """Test that openai provider embed calls api succeeds.

    ReqID: N/A"""
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


@pytest.mark.anyio
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


def test_lmstudio_provider_embed_calls_api_succeeds():
    """Test that lmstudio provider embed calls api succeeds.

    ReqID: N/A"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"embedding": [0.5, 0.6]}]}
    mock_response.raise_for_status.return_value = None
    with patch(
        "devsynth.adapters.provider_system.requests.post", return_value=mock_response
    ) as mock_post:
        provider = LMStudioProvider(endpoint="http://localhost:1234")
        result = provider.embed("text")
        assert result == [[0.5, 0.6]]
        mock_post.assert_called_once()


def test_embed_function_success_with_lmstudio_succeeds():
    """Test that embed function success with lmstudio succeeds.

    ReqID: N/A"""
    provider = LMStudioProvider(endpoint="http://localhost:1234")
    with (
        patch("devsynth.adapters.provider_system.get_provider", return_value=provider),
        patch("devsynth.adapters.provider_system.requests.post") as mock_post,
    ):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"embedding": [0.7, 0.8]}]}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp
        result = embed("text", provider_type="lmstudio", fallback=False)
        assert result == [[0.7, 0.8]]
        mock_post.assert_called_once()


@pytest.mark.anyio
async def test_aembed_function_success_with_lmstudio():
    provider = LMStudioProvider(endpoint="http://localhost:1234")
    async_client = AsyncMock()
    async_client.__aenter__.return_value = async_client
    async_client.__aexit__.return_value = None
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": [{"embedding": [0.9, 1.0]}]}
    mock_resp.raise_for_status.return_value = None
    async_client.post.return_value = mock_resp
    with (
        patch("devsynth.adapters.provider_system.get_provider", return_value=provider),
        patch(
            "devsynth.adapters.provider_system.httpx.AsyncClient",
            return_value=async_client,
        ),
    ):
        result = await aembed("text", provider_type="lmstudio", fallback=False)
        assert result == [[0.9, 1.0]]
        async_client.post.assert_called_once()


def test_lmstudio_provider_embed_error_succeeds():
    """Test that lmstudio provider embed error succeeds.

    ReqID: N/A"""
    with patch(
        "devsynth.adapters.provider_system.requests.post",
        side_effect=requests.exceptions.RequestException("boom"),
    ):
        provider = LMStudioProvider(endpoint="http://localhost:1234")
        with pytest.raises(ProviderError):
            provider.embed("text")


@pytest.mark.anyio
async def test_aembed_function_error_propagation():
    provider = LMStudioProvider(endpoint="http://localhost:1234")
    async_client = AsyncMock()
    async_client.__aenter__.return_value = async_client
    async_client.__aexit__.return_value = None
    async_client.post.side_effect = httpx.HTTPError("fail")
    with (
        patch("devsynth.adapters.provider_system.get_provider", return_value=provider),
        patch(
            "devsynth.adapters.provider_system.httpx.AsyncClient",
            return_value=async_client,
        ),
    ):
        with pytest.raises(ProviderError):
            await aembed("text", provider_type="lmstudio", fallback=False)
