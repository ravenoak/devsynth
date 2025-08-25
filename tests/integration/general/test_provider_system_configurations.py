"""Integration tests for provider system with different LLM configurations.

This test verifies that the provider system works correctly with different LLM configurations,
including different models, parameters, and provider combinations.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import responses

pytest.importorskip("lmstudio")
if not os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"):
    pytest.skip("LMStudio service not available", allow_module_level=True)

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

pytestmark = [pytest.mark.requires_resource("lmstudio")]


class TestProviderConfigurations:
    """Test the provider system with different LLM configurations.

    ReqID: N/A"""

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return {
            "choices": [{"message": {"content": "This is a mock response from OpenAI"}}]
        }

    @pytest.fixture
    def mock_lm_studio_response(self):
        """Mock LM Studio API response."""
        return {"choices": [{"text": "This is a mock response from LM Studio"}]}

    @responses.activate
    @pytest.mark.medium
    def test_openai_provider_with_different_models_has_expected(
        self, mock_openai_response
    ):
        """Test OpenAI provider with different models.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json=mock_openai_response,
            status=200,
        )
        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "test_key", "OPENAI_MODEL": "gpt-4"}
        ):
            provider = ProviderFactory.create_provider(ProviderType.OPENAI)
            assert provider.model == "gpt-4"
            result = provider.complete("Test prompt")
            assert result == "This is a mock response from OpenAI"
        responses.reset()
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json=mock_openai_response,
            status=200,
        )
        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "test_key", "OPENAI_MODEL": "gpt-3.5-turbo"}
        ):
            provider = ProviderFactory.create_provider(ProviderType.OPENAI)
            assert provider.model == "gpt-3.5-turbo"
            result = provider.complete("Test prompt")
            assert result == "This is a mock response from OpenAI"

    @responses.activate
    @pytest.mark.medium
    def test_openai_provider_with_different_parameters_has_expected(
        self, mock_openai_response
    ):
        """Test OpenAI provider with different parameters.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json=mock_openai_response,
            status=200,
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            provider = ProviderFactory.create_provider(ProviderType.OPENAI)
            result = provider.complete("Test prompt")
            assert result == "This is a mock response from OpenAI"
        responses.reset()
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json=mock_openai_response,
            status=200,
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            provider = ProviderFactory.create_provider(ProviderType.OPENAI)
            result = provider.complete(
                "Test prompt",
                parameters={"temperature": 0.7, "max_tokens": 100, "top_p": 0.9},
            )
            assert result == "This is a mock response from OpenAI"

    @responses.activate
    @pytest.mark.medium
    def test_lm_studio_provider_with_different_endpoints_has_expected(
        self, mock_lm_studio_response
    ):
        """Test LM Studio provider with different endpoints.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "http://127.0.0.1:1234/v1/chat/completions",
            json=mock_lm_studio_response,
            status=200,
        )
        with patch.dict(os.environ, {"LM_STUDIO_ENDPOINT": "http://127.0.0.1:1234"}):
            provider = ProviderFactory.create_provider(ProviderType.LMSTUDIO)
            result = provider.complete("Test prompt")
            assert result == "This is a mock response from LM Studio"
        responses.reset()
        responses.add(
            responses.POST,
            "http://custom-endpoint:5678/v1/chat/completions",
            json=mock_lm_studio_response,
            status=200,
        )
        with patch.dict(
            os.environ, {"LM_STUDIO_ENDPOINT": "http://custom-endpoint:5678"}
        ):
            provider = ProviderFactory.create_provider(ProviderType.LMSTUDIO)
            result = provider.complete("Test prompt")
            assert result == "This is a mock response from LM Studio"

    @responses.activate
    @pytest.mark.medium
    def test_lm_studio_provider_with_different_parameters_has_expected(
        self, mock_lm_studio_response
    ):
        """Test LM Studio provider with different parameters.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "http://127.0.0.1:1234/v1/chat/completions",
            json=mock_lm_studio_response,
            status=200,
        )
        with patch.dict(os.environ, {"LM_STUDIO_ENDPOINT": "http://127.0.0.1:1234"}):
            provider = ProviderFactory.create_provider(ProviderType.LMSTUDIO)
            result = provider.complete("Test prompt")
            assert result == "This is a mock response from LM Studio"
        responses.reset()
        responses.add(
            responses.POST,
            "http://127.0.0.1:1234/v1/chat/completions",
            json=mock_lm_studio_response,
            status=200,
        )
        with patch.dict(os.environ, {"LM_STUDIO_ENDPOINT": "http://127.0.0.1:1234"}):
            provider = ProviderFactory.create_provider(ProviderType.LMSTUDIO)
            result = provider.complete(
                "Test prompt",
                parameters={"temperature": 0.7, "max_tokens": 100, "top_p": 0.9},
            )
            assert result == "This is a mock response from LM Studio"

    @responses.activate
    @pytest.mark.medium
    def test_fallback_provider_with_different_configurations_has_expected(
        self, mock_openai_response, mock_lm_studio_response
    ):
        """Test fallback provider with different configurations.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json=mock_openai_response,
            status=200,
        )
        responses.add(
            responses.POST,
            "http://127.0.0.1:1234/v1/chat/completions",
            json=mock_lm_studio_response,
            status=200,
        )
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test_key",
                "LM_STUDIO_ENDPOINT": "http://127.0.0.1:1234",
            },
        ):
            openai_provider = ProviderFactory.create_provider(ProviderType.OPENAI)
            lm_studio_provider = ProviderFactory.create_provider(ProviderType.LMSTUDIO)
            fallback_provider = FallbackProvider(
                providers=[openai_provider, lm_studio_provider]
            )
            result = fallback_provider.complete("Test prompt")
            assert result == "This is a mock response from OpenAI"
        responses.reset()
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json={"error": "API error"},
            status=500,
        )
        responses.add(
            responses.POST,
            "http://127.0.0.1:1234/v1/chat/completions",
            json=mock_lm_studio_response,
            status=200,
        )
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test_key",
                "LM_STUDIO_ENDPOINT": "http://127.0.0.1:1234",
            },
        ):
            openai_provider = ProviderFactory.create_provider(ProviderType.OPENAI)
            lm_studio_provider = ProviderFactory.create_provider(ProviderType.LMSTUDIO)
            fallback_provider = FallbackProvider(
                providers=[openai_provider, lm_studio_provider]
            )
            result = fallback_provider.complete("Test prompt")
            assert result == "This is a mock response from LM Studio"

    @responses.activate
    @pytest.mark.medium
    def test_provider_system_with_different_default_providers_has_expected(
        self, mock_openai_response, mock_lm_studio_response
    ):
        """Test provider system with different default providers.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json=mock_openai_response,
            status=200,
        )
        with patch.dict(
            os.environ, {"DEVSYNTH_PROVIDER": "openai", "OPENAI_API_KEY": "test_key"}
        ):
            provider = get_provider()
            assert isinstance(provider, OpenAIProvider)
            result = complete("Test prompt")
            assert result == "This is a mock response from OpenAI"
        responses.reset()
        responses.add(
            responses.POST,
            "http://127.0.0.1:1234/v1/chat/completions",
            json=mock_lm_studio_response,
            status=200,
        )
        with patch.dict(
            os.environ,
            {
                "DEVSYNTH_PROVIDER": "lmstudio",
                "LM_STUDIO_ENDPOINT": "http://127.0.0.1:1234",
            },
        ):
            provider = get_provider()
            assert isinstance(provider, PS_LMStudioProvider)
            result = complete("Test prompt")
            assert result == "This is a mock response from LM Studio"

    @responses.activate
    @pytest.mark.medium
    def test_provider_system_with_context_aware_completion_has_expected(
        self, mock_openai_response
    ):
        """Test provider system with context-aware completion.

        ReqID: N/A"""
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json=mock_openai_response,
            status=200,
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            provider = ProviderFactory.create_provider(ProviderType.OPENAI)
            result = provider.complete_with_context(
                "Test prompt",
                [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"},
                    {"role": "assistant", "content": "The capital of France is Paris."},
                ],
            )
            assert result == "This is a mock response from OpenAI"
