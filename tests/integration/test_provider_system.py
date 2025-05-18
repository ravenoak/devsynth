"""
Integration tests for the provider system.

These tests verify the provider system can connect to both OpenAI and LM Studio,
with proper fallback and selection logic.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import responses
import json

from devsynth.adapters.provider_system import (
    get_provider_config,
    ProviderFactory,
    OpenAIProvider,
    LMStudioProvider,
    FallbackProvider,
    get_provider,
    complete,
    embed,
    ProviderType,
    ProviderError
)

# Skip these tests if no API keys are available
pytestmark = pytest.mark.skipif(
    os.environ.get("OPENAI_API_KEY") is None and os.environ.get("LM_STUDIO_ENDPOINT") is None,
    reason="No provider API keys or endpoints available"
)


class TestProviderConfig:
    """Test provider configuration loading."""

    def test_get_provider_config(self):
        """Test that provider config can be loaded."""
        config = get_provider_config()
        assert "default_provider" in config
        assert "openai" in config
        assert "lm_studio" in config

        # Config should match environment or defaults
        assert config["default_provider"] == os.environ.get("DEVSYNTH_PROVIDER", "openai")

        # OpenAI config
        assert config["openai"]["api_key"] == os.environ.get("OPENAI_API_KEY")
        assert config["openai"]["model"] == os.environ.get("OPENAI_MODEL", "gpt-4")

        # LM Studio config
        assert config["lm_studio"]["endpoint"] == os.environ.get(
            "LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")


class TestProviderFactory:
    """Test provider creation and selection."""

    def test_create_openai_provider(self):
        """Test OpenAI provider creation."""
        # Skip if no OpenAI API key
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        provider = ProviderFactory.create_provider(ProviderType.OPENAI.value)
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == os.environ.get("OPENAI_API_KEY")

    def test_create_lm_studio_provider(self):
        """Test LM Studio provider creation."""
        provider = ProviderFactory.create_provider(ProviderType.LM_STUDIO.value)
        assert isinstance(provider, LMStudioProvider)
        assert provider.endpoint == os.environ.get(
            "LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")

    def test_fallback_to_lm_studio(self):
        """Test fallback to LM Studio if OpenAI API key is missing."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with patch("devsynth.adapters.provider_system.get_provider_config") as mock_config:
                mock_config.return_value = {
                    "default_provider": "openai",
                    "openai": {"api_key": None},
                    "lm_studio": {"endpoint": "http://127.0.0.1:1234"}
                }
                provider = ProviderFactory.create_provider(ProviderType.OPENAI.value)
                assert isinstance(provider, LMStudioProvider)


@pytest.mark.integtest
class TestProviderIntegration:
    """Integration tests for provider functionality.

    These tests make actual API calls and should be run sparingly.
    """

    @responses.activate
    def test_openai_complete(self):
        """Test OpenAI completion with mocked response."""
        # Skip if no OpenAI API key
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        # Mock response
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json={
                "choices": [
                    {"message": {"content": "Test response"}}
                ]
            },
            status=200
        )

        provider = OpenAIProvider(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model="gpt-4"
        )
        response = provider.complete(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant."
        )

        assert response == "Test response"

    @responses.activate
    def test_lm_studio_complete(self):
        """Test LM Studio completion with mocked response."""
        # Mock response
        responses.add(
            responses.POST,
            "http://127.0.0.1:1234/v1/chat/completions",
            json={
                "choices": [
                    {"message": {"content": "Test response from LM Studio"}}
                ]
            },
            status=200
        )

        provider = LMStudioProvider(
            endpoint="http://127.0.0.1:1234"
        )
        response = provider.complete(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant."
        )

        assert response == "Test response from LM Studio"


class TestFallbackProvider:
    """Test fallback provider functionality."""

    def test_fallback_provider_complete(self):
        """Test fallback provider tries each provider in sequence."""
        # Create mock providers
        mock_provider1 = MagicMock()
        mock_provider1.complete.side_effect = ProviderError("Provider 1 failed")

        mock_provider2 = MagicMock()
        mock_provider2.complete.return_value = "Response from provider 2"

        # Create fallback provider with mock providers
        provider = FallbackProvider(providers=[mock_provider1, mock_provider2])

        # Call complete method
        response = provider.complete(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant."
        )

        # Verify that both providers were tried and the second one succeeded
        mock_provider1.complete.assert_called_once()
        mock_provider2.complete.assert_called_once()
        assert response == "Response from provider 2"

    def test_fallback_provider_all_fail(self):
        """Test fallback provider raises error if all providers fail."""
        # Create mock providers
        mock_provider1 = MagicMock()
        mock_provider1.complete.side_effect = ProviderError("Provider 1 failed")

        mock_provider2 = MagicMock()
        mock_provider2.complete.side_effect = ProviderError("Provider 2 failed")

        # Create fallback provider with mock providers
        provider = FallbackProvider(providers=[mock_provider1, mock_provider2])

        # Call complete method should raise error
        with pytest.raises(ProviderError):
            provider.complete(
                prompt="Test prompt",
                system_prompt="You are a helpful assistant."
            )


class TestSimplifiedAPI:
    """Test simplified API functions."""

    def test_get_provider(self):
        """Test get_provider function."""
        provider = get_provider(fallback=True)
        assert isinstance(provider, FallbackProvider)

        # Get specific provider
        with patch("devsynth.adapters.provider_system.ProviderFactory.create_provider") as mock_create:
            mock_create.return_value = MagicMock()
            provider = get_provider(provider_type=ProviderType.OPENAI.value, fallback=False)
            mock_create.assert_called_once_with(ProviderType.OPENAI.value)

    def test_complete_function(self):
        """Test complete function."""
        with patch("devsynth.adapters.provider_system.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.complete.return_value = "Test response"
            mock_get.return_value = mock_provider

            response = complete(
                prompt="Test prompt",
                system_prompt="You are a helpful assistant."
            )

            assert response == "Test response"
            mock_provider.complete.assert_called_once()

    def test_embed_function(self):
        """Test embed function."""
        with patch("devsynth.adapters.provider_system.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.embed.return_value = [[0.1, 0.2, 0.3]]
            mock_get.return_value = mock_provider

            response = embed(text="Test text")

            assert response == [[0.1, 0.2, 0.3]]
            mock_provider.embed.assert_called_once()
