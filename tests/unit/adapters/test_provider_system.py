import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest
import httpx
import requests
from devsynth.adapters import provider_system
from devsynth.adapters.provider_system import (
    ProviderError,
    ProviderFactory,
    BaseProvider,
    OpenAIProvider,
    LMStudioProvider,
    FallbackProvider,
    get_env_or_default,
    get_provider_config,
)
from devsynth.fallback import retry_with_exponential_backoff


def test_embed_success_succeeds():
    """Test that embed success succeeds.

    ReqID: N/A"""
    provider = MagicMock()
    provider.embed.return_value = [[1.0, 2.0]]
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = provider_system.embed("text", provider_type="lmstudio", fallback=False)
        assert result == [[1.0, 2.0]]
        provider.embed.assert_called_once()


def test_embed_error_succeeds():
    """Test that embed error succeeds.

    ReqID: N/A"""
    provider = MagicMock()
    provider.embed.side_effect = ProviderError("fail")
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            provider_system.embed("text", provider_type="lmstudio", fallback=False)


def test_aembed_success_succeeds():
    """Test that aembed success succeeds.

    ReqID: N/A"""
    provider = MagicMock()
    provider.aembed = AsyncMock(return_value=[[3.0, 4.0]])

    async def run_test():
        with patch.object(provider_system, "get_provider", return_value=provider):
            result = await provider_system.aembed(
                "text", provider_type="lmstudio", fallback=False
            )
            assert result == [[3.0, 4.0]]
            provider.aembed.assert_awaited_once()

    asyncio.run(run_test())


def test_aembed_error_succeeds():
    """Test that aembed error succeeds.

    ReqID: N/A"""
    provider = MagicMock()
    provider.aembed = AsyncMock(side_effect=ProviderError("boom"))

    async def run_test():
        with patch.object(provider_system, "get_provider", return_value=provider):
            with pytest.raises(ProviderError):
                await provider_system.aembed(
                    "text", provider_type="lmstudio", fallback=False
                )

    asyncio.run(run_test())


def test_complete_success_succeeds():
    """Test that complete success succeeds.

    ReqID: N/A"""
    provider = MagicMock()
    provider.complete.return_value = "Completed text"
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = provider_system.complete(
            "prompt", system_prompt="system", provider_type="openai", fallback=False
        )
        assert result == "Completed text"
        provider.complete.assert_called_once_with(
            prompt="prompt", system_prompt="system", temperature=0.7, max_tokens=2000
        )


def test_complete_error_succeeds():
    """Test that complete error succeeds.

    ReqID: N/A"""
    provider = MagicMock()
    provider.complete.side_effect = ProviderError("completion failed")
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            provider_system.complete("prompt", provider_type="openai", fallback=False)


def test_acomplete_success_succeeds():
    """Test that acomplete success succeeds.

    ReqID: N/A"""
    provider = MagicMock()
    provider.acomplete = AsyncMock(return_value="Async completed text")

    async def run_test():
        with patch.object(provider_system, "get_provider", return_value=provider):
            result = await provider_system.acomplete(
                "prompt", system_prompt="system", provider_type="openai", fallback=False
            )
            assert result == "Async completed text"
            provider.acomplete.assert_awaited_once_with(
                prompt="prompt",
                system_prompt="system",
                temperature=0.7,
                max_tokens=2000,
            )

    asyncio.run(run_test())


def test_acomplete_error_succeeds():
    """Test that acomplete error succeeds.

    ReqID: N/A"""
    provider = MagicMock()
    provider.acomplete = AsyncMock(side_effect=ProviderError("async completion failed"))

    async def run_test():
        with patch.object(provider_system, "get_provider", return_value=provider):
            with pytest.raises(ProviderError):
                await provider_system.acomplete(
                    "prompt", provider_type="openai", fallback=False
                )

    asyncio.run(run_test())


def test_provider_factory_create_provider_succeeds():
    """Test that provider factory create provider succeeds.

    ReqID: N/A"""
    with patch.object(provider_system, "get_provider_config") as mock_config:
        with patch.object(provider_system, "OpenAIProvider") as mock_openai:
            with patch.object(provider_system, "LMStudioProvider") as mock_lmstudio:
                mock_openai_instance = MagicMock(spec=OpenAIProvider)
                mock_openai.return_value = mock_openai_instance
                mock_lmstudio_instance = MagicMock(spec=LMStudioProvider)
                mock_lmstudio.return_value = mock_lmstudio_instance
                mock_config.return_value = {
                    "default_provider": "openai",
                    "openai": {
                        "api_key": "test_key",
                        "model": "gpt-4",
                        "base_url": "https://api.openai.com/v1",
                    },
                    "retry": {
                        "max_retries": 3,
                        "initial_delay": 1.0,
                        "exponential_base": 2.0,
                        "max_delay": 60.0,
                        "jitter": True,
                    },
                }
                factory = ProviderFactory()
                provider = factory.create_provider("openai")
                mock_openai.assert_called_once()
                assert provider is mock_openai_instance
                mock_openai.reset_mock()
                mock_config.return_value = {
                    "default_provider": "lmstudio",
                    "lmstudio": {
                        "endpoint": "http://test-endpoint",
                        "model": "default",
                    },
                    "retry": {
                        "max_retries": 3,
                        "initial_delay": 1.0,
                        "exponential_base": 2.0,
                        "max_delay": 60.0,
                        "jitter": True,
                    },
                }
                provider = factory.create_provider("lmstudio")
                mock_lmstudio.assert_called_once()
                assert provider is mock_lmstudio_instance
                mock_openai.reset_mock()
                mock_config.return_value = {
                    "default_provider": "openai",
                    "openai": {
                        "api_key": "default_key",
                        "model": "gpt-3.5-turbo",
                        "base_url": "https://api.openai.com/v1",
                    },
                    "retry": {
                        "max_retries": 3,
                        "initial_delay": 1.0,
                        "exponential_base": 2.0,
                        "max_delay": 60.0,
                        "jitter": True,
                    },
                }
                provider = factory.create_provider()
                mock_openai.assert_called_once()
                assert provider is mock_openai_instance


def test_get_provider_succeeds():
    """Test that get provider succeeds.

    ReqID: N/A"""
    with patch.object(ProviderFactory, "create_provider") as mock_create:
        mock_create.return_value = MagicMock(spec=OpenAIProvider)
        provider = provider_system.get_provider(provider_type="openai", fallback=True)
        assert isinstance(provider, FallbackProvider)
        provider = provider_system.get_provider(provider_type="openai", fallback=False)
        assert not isinstance(provider, FallbackProvider)
        mock_create.assert_called_with("openai")


def test_base_provider_methods_succeeds():
    """Test that base provider methods succeeds.

    ReqID: N/A"""
    provider = BaseProvider()
    with pytest.raises(NotImplementedError):
        provider.complete("test")
    with pytest.raises(NotImplementedError):
        provider.embed("test")
    with pytest.raises(NotImplementedError):
        asyncio.run(provider.acomplete("test"))
    with pytest.raises(NotImplementedError):
        asyncio.run(provider.aembed("test"))


@pytest.mark.parametrize(
    "provider_class,config",
    [
        (OpenAIProvider, {"api_key": "test_key", "model": "gpt-4"}),
        (LMStudioProvider, {"endpoint": "http://test-endpoint"}),
    ],
)
def test_provider_initialization_succeeds(provider_class, config):
    """Test that provider initialization succeeds.

    ReqID: N/A"""
    provider = provider_class(**config)
    assert provider is not None
    retry_decorator = provider.get_retry_decorator()
    assert callable(retry_decorator)


def test_fallback_provider_succeeds():
    """Test that fallback provider succeeds.

    ReqID: N/A"""
    provider1 = MagicMock(spec=BaseProvider)
    provider2 = MagicMock(spec=BaseProvider)
    provider1.complete.side_effect = ProviderError("Provider 1 failed")
    provider2.complete.return_value = "Success from provider 2"
    fallback = FallbackProvider(providers=[provider1, provider2])
    result = fallback.complete("test prompt")
    assert result == "Success from provider 2"
    provider1.complete.assert_called_once()
    provider2.complete.assert_called_once()
    provider2.complete.side_effect = ProviderError("Provider 2 failed")
    with pytest.raises(ProviderError):
        fallback.complete("test prompt")


def test_get_env_or_default_succeeds():
    """Test the get_env_or_default function.

    ReqID: N/A"""
    with patch.dict("os.environ", {"TEST_VAR": "test_value"}):
        assert get_env_or_default("TEST_VAR", "default") == "test_value"
    with patch.dict("os.environ", {}, clear=True):
        assert get_env_or_default("TEST_VAR", "default") == "default"
    with patch.dict("os.environ", {}, clear=True):
        assert get_env_or_default("TEST_VAR") is None


def test_get_provider_config_has_expected():
    """Test the get_provider_config function.

    ReqID: N/A"""
    get_provider_config.cache_clear()
    env_vars = {
        "DEVSYNTH_PROVIDER": "openai",
        "OPENAI_API_KEY": "test_key",
        "OPENAI_MODEL": "gpt-4",
        "LM_STUDIO_ENDPOINT": "http://test-endpoint",
    }
    with patch.dict("os.environ", env_vars, clear=True):
        config = get_provider_config()
        assert config["default_provider"] == "openai"
        assert config["openai"]["api_key"] == "test_key"
        assert config["openai"]["model"] == "gpt-4"
        assert config["lmstudio"]["endpoint"] == "http://test-endpoint"
    get_provider_config.cache_clear()
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"}, clear=True):
        config = get_provider_config()
        assert config["default_provider"] == "openai"
        assert config["openai"]["api_key"] == "test_key"
        assert "model" in config["openai"]


@patch("requests.post")
def test_openai_provider_complete_has_expected(mock_post):
    """Test the complete method of OpenAIProvider.

    ReqID: N/A"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test completion"}}]
    }
    mock_post.return_value = mock_response
    provider = OpenAIProvider(api_key="test_key", model="gpt-4")
    result = provider.complete("Test prompt", system_prompt="System prompt")
    assert result == "Test completion"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.openai.com/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer test_key"
    assert kwargs["json"]["model"] == "gpt-4"
    assert kwargs["json"]["messages"][0]["content"] == "System prompt"
    assert kwargs["json"]["messages"][1]["content"] == "Test prompt"


@patch("requests.post")
def test_openai_provider_complete_error_raises_error(mock_post):
    """Test error handling in the complete method of OpenAIProvider.

    ReqID: N/A"""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": {"message": "Bad request"}}
    mock_post.return_value = mock_response
    provider = OpenAIProvider(api_key="test_key", model="gpt-4")
    with pytest.raises(ProviderError) as excinfo:
        provider.complete("Test prompt")
    assert "Bad request" in str(excinfo.value)


@patch("requests.post")
def test_openai_provider_complete_retry_has_expected(mock_post):
    """Test retry mechanism in the complete method of OpenAIProvider.

    ReqID: FR-89"""
    with patch(
        "devsynth.adapters.provider_system.retry_with_exponential_backoff"
    ) as mock_retry:
        mock_retry.return_value = lambda func: func
        error_response = MagicMock()
        error_response.status_code = 429
        error_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Client Error"
        )
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Test completion"}}]
        }
        mock_post.side_effect = [error_response, success_response]
        provider = OpenAIProvider(api_key="test_key", model="gpt-4")
        try:
            provider.complete("Test prompt")
        except ProviderError:
            mock_post.side_effect = [success_response]
            result = provider.complete("Test prompt")
            assert result == "Test completion"
        assert mock_retry.call_count >= 1
        retry_calls_with_correct_params = [
            call
            for call in mock_retry.call_args_list
            if call[1].get("retryable_exceptions")
            == (requests.exceptions.RequestException,)
            and call[1].get("should_retry") is provider._should_retry
        ]
        assert len(retry_calls_with_correct_params) >= 1


@patch("httpx.AsyncClient.post")
def test_openai_provider_acomplete_has_expected(mock_post):
    """Test the acomplete method of OpenAIProvider.

    ReqID: N/A"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Async test completion"}}]
    }
    mock_post.return_value = mock_response
    provider = OpenAIProvider(api_key="test_key", model="gpt-4")

    async def run_test():
        result = await provider.acomplete("Test prompt", system_prompt="System prompt")
        assert result == "Async test completion"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.openai.com/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer test_key"
        assert kwargs["json"]["model"] == "gpt-4"
        assert kwargs["json"]["messages"][0]["content"] == "System prompt"
        assert kwargs["json"]["messages"][1]["content"] == "Test prompt"

    asyncio.run(run_test())


@patch("requests.post")
def test_openai_provider_embed_has_expected(mock_post):
    """Test the embed method of OpenAIProvider.

    ReqID: N/A"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
    mock_post.return_value = mock_response
    provider = OpenAIProvider(api_key="test_key", model="gpt-4")
    result = provider.embed("Test text")
    assert result == [[0.1, 0.2, 0.3]]
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.openai.com/v1/embeddings"
    assert kwargs["headers"]["Authorization"] == "Bearer test_key"
    assert kwargs["json"]["input"] == ["Test text"]


@patch("requests.post")
def test_lmstudio_provider_complete_has_expected(mock_post):
    """Test the complete method of LMStudioProvider.

    ReqID: N/A"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "LM Studio completion"}}]
    }
    mock_post.return_value = mock_response
    provider = LMStudioProvider(endpoint="http://test-endpoint")
    result = provider.complete("Test prompt", system_prompt="System prompt")
    assert result == "LM Studio completion"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://test-endpoint/v1/chat/completions"
    assert kwargs["json"]["messages"][0]["content"] == "System prompt"
    assert kwargs["json"]["messages"][1]["content"] == "Test prompt"


def test_fallback_provider_async_methods_has_expected():
    """Test the async methods of FallbackProvider.

    ReqID: N/A"""
    provider1 = MagicMock(spec=BaseProvider)
    provider2 = MagicMock(spec=BaseProvider)
    provider1.acomplete = AsyncMock(side_effect=ProviderError("Provider 1 failed"))
    provider2.acomplete = AsyncMock(return_value="Async success from provider 2")
    provider1.aembed = AsyncMock(side_effect=ProviderError("Provider 1 failed"))
    provider2.aembed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    fallback = FallbackProvider(providers=[provider1, provider2])

    async def run_test():
        result = await fallback.acomplete("test prompt")
        assert result == "Async success from provider 2"
        provider1.acomplete.assert_awaited_once()
        provider2.acomplete.assert_awaited_once()
        result = await fallback.aembed("test text")
        assert result == [[0.1, 0.2, 0.3]]
        provider1.aembed.assert_awaited_once()
        provider2.aembed.assert_awaited_once()
        provider2.acomplete.side_effect = ProviderError("Provider 2 failed")
        with pytest.raises(ProviderError):
            await fallback.acomplete("test prompt")

    asyncio.run(run_test())


def test_provider_with_empty_inputs_has_expected():
    """Test providers with empty inputs.

    ReqID: N/A"""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Empty prompt response"}}]
        }
        mock_post.return_value = mock_response
        provider = OpenAIProvider(api_key="test_key")
        result = provider.complete("")
        assert result == "Empty prompt response"
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["messages"][0]["content"] == ""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Empty prompt response"}}]
        }
        mock_post.return_value = mock_response
        provider = LMStudioProvider()
        result = provider.complete("")
        assert result == "Empty prompt response"


def test_provider_factory_injected_config_selects_provider():
    """ProviderFactory should respect injected configuration."""
    custom_config = {
        "default_provider": "openai",
        "openai": {"api_key": "x", "model": "gpt-4", "base_url": "http://api"},
        "lmstudio": {"endpoint": "http://lm", "model": "default"},
        "retry": {
            "max_retries": 1,
            "initial_delay": 0,
            "exponential_base": 2,
            "max_delay": 1,
            "jitter": False,
        },
    }
    provider = ProviderFactory.create_provider("openai", config=custom_config)
    assert isinstance(provider, OpenAIProvider)
    provider = ProviderFactory.create_provider("lmstudio", config=custom_config)
    assert isinstance(provider, LMStudioProvider)
    provider = ProviderFactory.create_provider(config=custom_config)
    assert isinstance(provider, OpenAIProvider)


def test_fallback_provider_respects_order(monkeypatch):
    """FallbackProvider should instantiate providers based on order."""
    created: list[str] = []

    class FakeFactory:
        @staticmethod
        def create_provider(provider_type: str, **kwargs):
            created.append(provider_type)
            return MagicMock(spec=BaseProvider)

    config = {
        "fallback": {"enabled": True, "order": ["openai", "lmstudio"]},
        "circuit_breaker": {"enabled": False},
        "retry": {
            "max_retries": 1,
            "initial_delay": 0,
            "exponential_base": 2,
            "max_delay": 1,
            "jitter": False,
        },
    }

    fallback = FallbackProvider(config=config, provider_factory=FakeFactory)
    assert created == ["openai", "lmstudio"]
    assert len(fallback.providers) == 2
