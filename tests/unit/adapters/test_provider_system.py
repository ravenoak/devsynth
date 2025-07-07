import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from devsynth.adapters import provider_system
from devsynth.adapters.provider_system import (
    ProviderError, ProviderFactory, BaseProvider, 
    OpenAIProvider, LMStudioProvider, FallbackProvider
)


def test_embed_success():
    provider = MagicMock()
    provider.embed.return_value = [[1.0, 2.0]]
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = provider_system.embed(
            "text", provider_type="lm_studio", fallback=False
        )
        assert result == [[1.0, 2.0]]
        provider.embed.assert_called_once()


def test_embed_error():
    provider = MagicMock()
    provider.embed.side_effect = ProviderError("fail")
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            provider_system.embed("text", provider_type="lm_studio", fallback=False)


@pytest.mark.asyncio
async def test_aembed_success():
    provider = MagicMock()
    provider.aembed = AsyncMock(return_value=[[3.0, 4.0]])
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = await provider_system.aembed(
            "text", provider_type="lm_studio", fallback=False
        )
        assert result == [[3.0, 4.0]]
        provider.aembed.assert_called_once()


@pytest.mark.asyncio
async def test_aembed_error():
    provider = MagicMock()
    provider.aembed = AsyncMock(side_effect=ProviderError("boom"))
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            await provider_system.aembed(
                "text", provider_type="lm_studio", fallback=False
            )


def test_complete_success():
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


def test_complete_error():
    provider = MagicMock()
    provider.complete.side_effect = ProviderError("completion failed")
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            provider_system.complete(
                "prompt", provider_type="openai", fallback=False
            )


@pytest.mark.asyncio
async def test_acomplete_success():
    provider = MagicMock()
    provider.acomplete = AsyncMock(return_value="Async completed text")
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = await provider_system.acomplete(
            "prompt", system_prompt="system", provider_type="openai", fallback=False
        )
        assert result == "Async completed text"
        provider.acomplete.assert_called_once_with(
            prompt="prompt", system_prompt="system", temperature=0.7, max_tokens=2000
        )


@pytest.mark.asyncio
async def test_acomplete_error():
    provider = MagicMock()
    provider.acomplete = AsyncMock(side_effect=ProviderError("async completion failed"))
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            await provider_system.acomplete(
                "prompt", provider_type="openai", fallback=False
            )


def test_provider_factory_create_provider():
    with patch.object(provider_system, "get_provider_config") as mock_config:
        # Mock the provider classes to avoid actual initialization
        with patch.object(provider_system, "OpenAIProvider") as mock_openai:
            with patch.object(provider_system, "LMStudioProvider") as mock_lmstudio:
                # Configure mocks
                mock_openai_instance = MagicMock(spec=OpenAIProvider)
                mock_openai.return_value = mock_openai_instance

                mock_lmstudio_instance = MagicMock(spec=LMStudioProvider)
                mock_lmstudio.return_value = mock_lmstudio_instance

                # Test OpenAI provider creation
                mock_config.return_value = {
                    "provider": "openai",
                    "openai_api_key": "test_key",
                    "openai_model": "gpt-4",
                }
                factory = ProviderFactory()
                provider = factory.create_provider("openai")
                mock_openai.assert_called_once()
                assert provider is mock_openai_instance

                # Reset mocks
                mock_openai.reset_mock()

                # Test LM Studio provider creation
                mock_config.return_value = {
                    "provider": "lm_studio",
                    "lm_studio_endpoint": "http://test-endpoint",
                }
                provider = factory.create_provider("lm_studio")
                mock_lmstudio.assert_called_once()
                assert provider is mock_lmstudio_instance

                # Reset mocks
                mock_openai.reset_mock()

                # Test default provider creation
                mock_config.return_value = {
                    "provider": "openai",
                    "openai_api_key": "default_key",
                    "openai_model": "gpt-3.5-turbo",
                }
                provider = factory.create_provider()
                mock_openai.assert_called_once()
                assert provider is mock_openai_instance


def test_get_provider():
    with patch.object(ProviderFactory, "create_provider") as mock_create:
        # Test with fallback=True
        mock_create.return_value = MagicMock(spec=OpenAIProvider)
        provider = provider_system.get_provider(provider_type="openai", fallback=True)
        assert isinstance(provider, FallbackProvider)

        # Test with fallback=False
        provider = provider_system.get_provider(provider_type="openai", fallback=False)
        assert not isinstance(provider, FallbackProvider)
        mock_create.assert_called_with("openai")


def test_base_provider_methods():
    # Test that abstract methods raise NotImplementedError
    provider = BaseProvider()

    with pytest.raises(NotImplementedError):
        provider.complete("test")

    with pytest.raises(NotImplementedError):
        provider.embed("test")

    with pytest.raises(NotImplementedError):
        asyncio.run(provider.acomplete("test"))

    with pytest.raises(NotImplementedError):
        asyncio.run(provider.aembed("test"))


@pytest.mark.parametrize("provider_class,config", [
    (OpenAIProvider, {"api_key": "test_key", "model": "gpt-4"}),
    (LMStudioProvider, {"endpoint": "http://test-endpoint"}),
])
def test_provider_initialization(provider_class, config):
    provider = provider_class(**config)
    assert provider is not None

    # Test retry decorator
    retry_decorator = provider.get_retry_decorator()
    assert callable(retry_decorator)


def test_fallback_provider():
    # Create mock providers
    provider1 = MagicMock(spec=BaseProvider)
    provider2 = MagicMock(spec=BaseProvider)

    # Configure the first provider to fail, second to succeed
    provider1.complete.side_effect = ProviderError("Provider 1 failed")
    provider2.complete.return_value = "Success from provider 2"

    # Create fallback provider with the mock providers
    fallback = FallbackProvider(providers=[provider1, provider2])

    # Test complete method with fallback
    result = fallback.complete("test prompt")
    assert result == "Success from provider 2"
    provider1.complete.assert_called_once()
    provider2.complete.assert_called_once()

    # Test when all providers fail
    provider2.complete.side_effect = ProviderError("Provider 2 failed")
    with pytest.raises(ProviderError):
        fallback.complete("test prompt")
