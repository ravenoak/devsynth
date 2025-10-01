"""
Integration tests for the provider system.

These tests verify the provider system can connect to both OpenAI and LM Studio,
with proper fallback and selection logic.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import responses

pytest.importorskip("lmstudio")
if not os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"):
    pytest.skip("LMStudio service not available", allow_module_level=True)
if not os.environ.get("DEVSYNTH_RESOURCE_OPENAI_AVAILABLE"):
    pytest.skip("OpenAI service not available", allow_module_level=True)

from devsynth.adapters.provider_system import (
    FallbackProvider,
)
from devsynth.adapters.provider_system import LMStudioProvider as PS_LMStudioProvider
from devsynth.adapters.provider_system import (
    OpenAIProvider,
    ProviderError,
    ProviderFactory,
    ProviderType,
    complete,
    embed,
    get_provider,
    get_provider_config,
)
from devsynth.application.llm.providers import LMStudioProvider

pytestmark = [
    pytest.mark.requires_resource("lmstudio"),
    pytest.mark.requires_resource("openai"),
]


class TestProviderConfig:
    """Test provider configuration loading.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_get_provider_config_has_expected(self):
        """Test that provider config can be loaded.

        ReqID: N/A"""
        config = get_provider_config()
        assert "default_provider" in config
        assert "openai" in config
        assert "lmstudio" in config
        assert config["default_provider"] == os.environ.get(
            "DEVSYNTH_PROVIDER", "openai"
        )
        assert config["openai"]["api_key"] == os.environ.get("OPENAI_API_KEY")
        assert config["openai"]["model"] == os.environ.get("OPENAI_MODEL", "gpt-4")
        assert config["lmstudio"]["endpoint"] == os.environ.get(
            "LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234"
        )


class TestProviderFactory:
    """Test provider creation and selection.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_create_openai_provider_has_expected(self):
        """Test OpenAI provider creation.

        ReqID: N/A"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
            with patch(
                "devsynth.adapters.provider_system.get_provider_config"
            ) as mock_config:
                mock_config.return_value = {
                    "default_provider": "openai",
                    "openai": {
                        "api_key": "test-api-key",
                        "model": "gpt-4",
                        "base_url": "https://api.openai.com/v1",
                    },
                    "lmstudio": {
                        "endpoint": "http://127.0.0.1:1234",
                        "model": "default",
                    },
                }
                provider = ProviderFactory.create_provider(ProviderType.OPENAI.value)
                assert isinstance(provider, OpenAIProvider)
                assert provider.api_key == "test-api-key"

    @pytest.mark.medium
    def test_create_lm_studio_provider_has_expected(self):
        """Test LM Studio provider creation.

        ReqID: N/A"""
        with patch(
            "devsynth.adapters.provider_system.get_provider_config"
        ) as mock_config:
            mock_config.return_value = {
                "default_provider": "lmstudio",
                "openai": {
                    "api_key": None,
                    "model": "gpt-4",
                    "base_url": "https://api.openai.com/v1",
                },
                "lmstudio": {
                    "endpoint": "http://test-endpoint:1234",
                    "model": "test-model",
                },
            }
            provider = ProviderFactory.create_provider(ProviderType.LMSTUDIO.value)
            assert isinstance(provider, PS_LMStudioProvider)
            assert provider.endpoint == "http://test-endpoint:1234"
            assert provider.model == "test-model"

    @pytest.mark.medium
    def test_fallback_to_lm_studio_succeeds(self):
        """Test fallback to LM Studio if OpenAI API key is missing.

        ReqID: N/A"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with patch(
                "devsynth.adapters.provider_system.get_provider_config"
            ) as mock_config:
                mock_config.return_value = {
                    "default_provider": "openai",
                    "openai": {
                        "api_key": None,
                        "model": "gpt-4",
                        "base_url": "https://api.openai.com/v1",
                    },
                    "lmstudio": {
                        "endpoint": "http://127.0.0.1:1234",
                        "model": "default",
                    },
                }
                provider = ProviderFactory.create_provider(ProviderType.OPENAI.value)
            assert isinstance(provider, PS_LMStudioProvider)


@pytest.mark.integtest
class TestProviderIntegration:
    """Integration tests for provider functionality.

    These tests make actual API calls and should be run sparingly.

    ReqID: N/A"""

    @responses.activate
    @pytest.mark.medium
    def test_openai_complete_succeeds(self):
        """Test OpenAI completion with mocked response.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json={"choices": [{"message": {"content": "Test response"}}]},
            status=200,
        )
        provider = OpenAIProvider(api_key="test-api-key", model="gpt-4")
        response = provider.complete(
            prompt="Test prompt", system_prompt="You are a helpful assistant."
        )
        assert response == "Test response"

    @responses.activate
    @pytest.mark.medium
    def test_lm_studio_complete_succeeds(self):
        """Test LM Studio completion with mocked response.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "http://127.0.0.1:1234/v1/chat/completions",
            json={
                "choices": [{"message": {"content": "Test response from LM Studio"}}]
            },
            status=200,
        )
        provider = PS_LMStudioProvider(endpoint="http://127.0.0.1:1234")
        response = provider.complete(
            prompt="Test prompt", system_prompt="You are a helpful assistant."
        )
        assert response == "Test response from LM Studio"


class TestFallbackProvider:
    """Test fallback provider functionality.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_fallback_provider_complete_has_expected(self):
        """Test fallback provider tries each provider in sequence.

        ReqID: N/A"""
        mock_provider1 = MagicMock()
        mock_provider1.complete.side_effect = ProviderError("Provider 1 failed")
        mock_provider2 = MagicMock()
        mock_provider2.complete.return_value = "Response from provider 2"
        provider = FallbackProvider(providers=[mock_provider1, mock_provider2])
        response = provider.complete(
            prompt="Test prompt", system_prompt="You are a helpful assistant."
        )
        mock_provider1.complete.assert_called_once()
        mock_provider2.complete.assert_called_once()
        assert response == "Response from provider 2"

    @pytest.mark.medium
    def test_fallback_provider_all_fail_fails(self):
        """Test fallback provider raises error if all providers fail.

        ReqID: N/A"""
        mock_provider1 = MagicMock()
        mock_provider1.complete.side_effect = ProviderError("Provider 1 failed")
        mock_provider2 = MagicMock()
        mock_provider2.complete.side_effect = ProviderError("Provider 2 failed")
        provider = FallbackProvider(providers=[mock_provider1, mock_provider2])
        with pytest.raises(ProviderError):
            provider.complete(
                prompt="Test prompt", system_prompt="You are a helpful assistant."
            )


class TestSimplifiedAPI:
    """Test simplified API functions.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_get_provider_has_expected(self):
        """Test get_provider function.

        ReqID: N/A"""
        provider = get_provider(fallback=True)
        assert isinstance(provider, FallbackProvider)
        with patch(
            "devsynth.adapters.provider_system.ProviderFactory.create_provider"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            provider = get_provider(
                provider_type=ProviderType.OPENAI.value, fallback=False
            )
            mock_create.assert_called_once_with(ProviderType.OPENAI.value)

    @pytest.mark.medium
    def test_complete_function_succeeds(self):
        """Test complete function.

        ReqID: N/A"""
        with patch("devsynth.adapters.provider_system.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.complete.return_value = "Test response"
            mock_get.return_value = mock_provider
            response = complete(
                prompt="Test prompt", system_prompt="You are a helpful assistant."
            )
            assert response == "Test response"
            mock_provider.complete.assert_called_once()

    @pytest.mark.medium
    def test_embed_function_succeeds(self):
        """Test embed function.

        ReqID: N/A"""
        with patch("devsynth.adapters.provider_system.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.embed.return_value = [[0.1, 0.2, 0.3]]
            mock_get.return_value = mock_provider
            response = embed(text="Test text")
            assert response == [[0.1, 0.2, 0.3]]
            mock_provider.embed.assert_called_once()
