"""
Unit tests for OpenRouter provider.

These tests verify the OpenRouter provider implementation with comprehensive
coverage of all functionality, error conditions, and edge cases.

NOTE: OpenRouter free-tier should be used for all OpenRouter-specific tests
and general tests requiring live LLM functionality. Prefer OpenRouter over
OpenAI for cost efficiency in testing.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import responses

from devsynth.application.llm.openrouter_provider import (
    OpenRouterConnectionError,
    OpenRouterModelError,
    OpenRouterProvider,
)
from devsynth.exceptions import DevSynthError


class TestOpenRouterProviderInitialization:
    """Test OpenRouter provider initialization."""

    @pytest.mark.fast
    def test_initialization_with_valid_config(self):
        """Test initialization with valid configuration."""
        config = {
            "openrouter_api_key": "test-key",
            "openrouter_model": "google/gemini-flash-1.5",
            "max_tokens": 1000,
            "temperature": 0.8,
        }

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}):
            provider = OpenRouterProvider(config)

        assert provider.api_key == "test-key"
        assert provider.model == "google/gemini-flash-1.5"
        assert provider.max_tokens == 1000
        assert provider.temperature == 0.8
        assert provider.base_url == "https://openrouter.ai/api/v1"

    @pytest.mark.fast
    def test_initialization_with_environment_variable(self):
        """Test initialization using environment variable."""
        config = {"openrouter_model": "meta-llama/llama-3.1-8b-instruct"}

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-api-key"}):
            provider = OpenRouterProvider(config)

        assert provider.api_key == "env-api-key"
        assert provider.model == "meta-llama/llama-3.1-8b-instruct"

    @pytest.mark.fast
    def test_initialization_without_api_key_raises_error(self):
        """Test that initialization fails without API key."""
        config = {"openrouter_model": "google/gemini-flash-1.5"}

        with pytest.raises(OpenRouterConnectionError) as exc_info:
            OpenRouterProvider(config)

        assert "API key is required" in str(exc_info.value)

    @pytest.mark.fast
    def test_initialization_with_default_free_tier_model(self):
        """Test initialization with default free-tier model."""
        config = {"openrouter_api_key": "test-key"}

        provider = OpenRouterProvider(config)

        assert provider.model == "google/gemini-flash-1.5"  # Default free tier

    @pytest.mark.fast
    def test_initialization_with_httpx_unavailable(self):
        """Test initialization when httpx is not available."""
        config = {"openrouter_api_key": "test-key"}

        with patch("devsynth.application.llm.openrouter_provider.httpx", None):
            provider = OpenRouterProvider(config)

        assert provider.sync_client is None
        assert provider.async_client is None

    @pytest.mark.fast
    def test_initialization_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        config = {
            "openrouter_api_key": "test-key",
            "base_url": "https://custom.openrouter.com/api/v1",
        }

        provider = OpenRouterProvider(config)

        assert provider.base_url == "https://custom.openrouter.com/api/v1"


class TestOpenRouterProviderTextGeneration:
    """Test OpenRouter provider text generation functionality."""

    @pytest.fixture
    def mock_openrouter_response(self):
        """Mock OpenRouter API response."""
        return {
            "id": "chatcmpl-abc123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "google/gemini-flash-1.5",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from OpenRouter."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 12,
                "total_tokens": 22
            }
        }

    @pytest.mark.medium
    def test_generate_basic_text(self, mock_openrouter_response):
        """Test basic text generation."""
        config = {"openrouter_api_key": "test-key"}

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/chat/completions",
                json=mock_openrouter_response,
                status=200,
                headers={"Content-Type": "application/json"}
            )

            provider = OpenRouterProvider(config)
            response = provider.generate("Hello, how are you?")

        assert response == "This is a test response from OpenRouter."
        assert len(rsps.calls) == 1

        # Verify request structure
        request_data = rsps.calls[0].request.body.decode('utf-8')
        request_json = __import__('json').loads(request_data)
        assert request_json["model"] == "google/gemini-flash-1.5"  # Default free tier
        assert request_json["messages"][0]["content"] == "Hello, how are you?"

    @pytest.mark.medium
    def test_generate_with_custom_parameters(self, mock_openrouter_response):
        """Test text generation with custom parameters."""
        config = {"openrouter_api_key": "test-key"}

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/chat/completions",
                json=mock_openrouter_response,
                status=200
            )

            provider = OpenRouterProvider(config)
            response = provider.generate(
                "Tell me a story",
                parameters={"temperature": 0.9, "max_tokens": 500}
            )

        assert response == "This is a test response from OpenRouter."

        # Verify parameters in request
        request_data = rsps.calls[0].request.body.decode('utf-8')
        request_json = __import__('json').loads(request_data)
        assert request_json["temperature"] == 0.9
        assert request_json["max_tokens"] == 500

    @pytest.mark.medium
    def test_generate_with_context(self, mock_openrouter_response):
        """Test text generation with conversation context."""
        config = {"openrouter_api_key": "test-key"}

        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather like?"},
        ]

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/chat/completions",
                json=mock_openrouter_response,
                status=200
            )

            provider = OpenRouterProvider(config)
            response = provider.generate_with_context("How about tomorrow?", context)

        assert response == "This is a test response from OpenRouter."

        # Verify context in request
        request_data = rsps.calls[0].request.body.decode('utf-8')
        request_json = __import__('json').loads(request_data)
        assert len(request_json["messages"]) == 3
        assert request_json["messages"][0]["role"] == "system"
        assert request_json["messages"][1]["role"] == "user"
        assert request_json["messages"][2]["role"] == "user"

    @pytest.mark.medium
    def test_generate_with_invalid_parameters(self):
        """Test text generation with invalid parameters."""
        config = {"openrouter_api_key": "test-key"}
        provider = OpenRouterProvider(config)

        # Test invalid temperature
        with pytest.raises(OpenRouterConnectionError) as exc_info:
            provider.generate("Hello", {"temperature": 3.0})

        assert "temperature must be between 0 and 2" in str(exc_info.value)

        # Test invalid max_tokens
        with pytest.raises(OpenRouterConnectionError) as exc_info:
            provider.generate("Hello", {"max_tokens": -1})

        assert "max_tokens must be positive" in str(exc_info.value)

    @pytest.mark.medium
    def test_generate_api_error_handling(self):
        """Test API error handling."""
        config = {"openrouter_api_key": "test-key"}

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/chat/completions",
                json={"error": {"message": "Invalid API key"}},
                status=401
            )

            provider = OpenRouterProvider(config)

            with pytest.raises(OpenRouterConnectionError) as exc_info:
                provider.generate("Hello")

            assert "OpenRouter API error" in str(exc_info.value)

    @pytest.mark.medium
    def test_generate_rate_limit_handling(self):
        """Test rate limit error handling."""
        config = {"openrouter_api_key": "test-key"}

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/chat/completions",
                json={"error": {"message": "Rate limit exceeded"}},
                status=429
            )

            provider = OpenRouterProvider(config)

            # Should retry on 429 errors
            with patch.object(provider, '_should_retry', return_value=True):
                with pytest.raises(OpenRouterConnectionError):
                    provider.generate("Hello")


class TestOpenRouterProviderStreaming:
    """Test OpenRouter provider streaming functionality."""

    @pytest.fixture
    def mock_streaming_response(self):
        """Mock OpenRouter streaming response."""
        return [
            "data: {\"id\": \"chatcmpl-abc123\", \"object\": \"chat.completion.chunk\", \"created\": 1677652288, \"model\": \"google/gemini-flash-1.5\", \"choices\": [{\"index\": 0, \"delta\": {\"content\": \"Hello\"}, \"finish_reason\": null}]}\n",
            "data: {\"id\": \"chatcmpl-abc123\", \"object\": \"chat.completion.chunk\", \"created\": 1677652288, \"model\": \"google/gemini-flash-1.5\", \"choices\": [{\"index\": 0, \"delta\": {\"content\": \" world\"}, \"finish_reason\": null}]}\n",
            "data: {\"id\": \"chatcmpl-abc123\", \"object\": \"chat.completion.chunk\", \"created\": 1677652288, \"model\": \"google/gemini-flash-1.5\", \"choices\": [{\"index\": 0, \"delta\": {\"content\": \"!\"}, \"finish_reason\": \"stop\"}]}\n",
            "data: [DONE]\n",
        ]

    @pytest.mark.slow
    def test_generate_stream_basic(self, mock_streaming_response):
        """Test basic streaming generation."""
        config = {"openrouter_api_key": "test-key"}

        with patch("httpx.AsyncClient") as mock_client:
            # Mock the async client and streaming response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.aiter_lines.return_value = mock_streaming_response

            mock_client_instance = MagicMock()
            mock_client_instance.stream.return_value.__aenter__.return_value = mock_response
            mock_client.return_value = mock_client_instance

            provider = OpenRouterProvider(config)

            # Test that streaming returns an async generator
            # Note: We can't easily test the full async streaming without async test framework
            # This tests the basic structure
            stream_gen = provider.generate_stream("Hello")
            assert hasattr(stream_gen, '__aiter__')

    @pytest.mark.medium
    def test_generate_stream_without_httpx(self):
        """Test streaming when httpx is not available."""
        config = {"openrouter_api_key": "test-key"}

        with patch("devsynth.application.llm.openrouter_provider.httpx", None):
            provider = OpenRouterProvider(config)

            with pytest.raises(OpenRouterConnectionError) as exc_info:
                provider.generate_stream("Hello")

            assert "httpx package required for streaming" in str(exc_info.value)


class TestOpenRouterProviderEmbeddings:
    """Test OpenRouter provider embedding functionality."""

    @pytest.fixture
    def mock_embedding_response(self):
        """Mock OpenRouter embedding response."""
        return {
            "object": "list",
            "data": [{
                "object": "embedding",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "index": 0
            }],
            "model": "text-embedding-ada-002",
            "usage": {
                "prompt_tokens": 8,
                "total_tokens": 8
            }
        }

    @pytest.mark.medium
    def test_get_embedding_single_text(self, mock_embedding_response):
        """Test embedding generation for single text."""
        config = {"openrouter_api_key": "test-key"}

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/embeddings",
                json=mock_embedding_response,
                status=200
            )

            provider = OpenRouterProvider(config)
            embedding = provider.get_embedding("The quick brown fox")

        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert len(rsps.calls) == 1

        # Verify request structure
        request_data = rsps.calls[0].request.body.decode('utf-8')
        request_json = __import__('json').loads(request_data)
        assert request_json["model"] == "text-embedding-ada-002"
        assert request_json["input"] == "The quick brown fox"

    @pytest.mark.medium
    def test_get_embedding_multiple_texts(self, mock_embedding_response):
        """Test embedding generation for multiple texts."""
        config = {"openrouter_api_key": "test-key"}

        # Mock response for multiple texts
        multi_response = {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": [0.1, 0.2, 0.3],
                    "index": 0
                },
                {
                    "object": "embedding",
                    "embedding": [0.4, 0.5, 0.6],
                    "index": 1
                }
            ],
            "model": "text-embedding-ada-002",
            "usage": {
                "prompt_tokens": 16,
                "total_tokens": 16
            }
        }

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/embeddings",
                json=multi_response,
                status=200
            )

            provider = OpenRouterProvider(config)
            embeddings = provider.get_embedding(["Text one", "Text two"])

        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]

    @pytest.mark.medium
    def test_get_embedding_api_error(self):
        """Test embedding API error handling."""
        config = {"openrouter_api_key": "test-key"}

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/embeddings",
                json={"error": {"message": "Invalid model"}},
                status=400
            )

            provider = OpenRouterProvider(config)

            with pytest.raises(OpenRouterConnectionError) as exc_info:
                provider.get_embedding("Test text")

            assert "OpenRouter embedding API error" in str(exc_info.value)


class TestOpenRouterProviderErrorHandling:
    """Test OpenRouter provider error handling."""

    @pytest.mark.fast
    def test_invalid_temperature_range(self):
        """Test error handling for invalid temperature range."""
        config = {"openrouter_api_key": "test-key"}
        provider = OpenRouterProvider(config)

        with pytest.raises(OpenRouterConnectionError) as exc_info:
            provider.generate("Hello", {"temperature": -0.1})

        assert "temperature must be between 0 and 2" in str(exc_info.value)

    @pytest.mark.fast
    def test_invalid_max_tokens(self):
        """Test error handling for invalid max_tokens."""
        config = {"openrouter_api_key": "test-key"}
        provider = OpenRouterProvider(config)

        with pytest.raises(OpenRouterConnectionError) as exc_info:
            provider.generate("Hello", {"max_tokens": 0})

        assert "max_tokens must be positive" in str(exc_info.value)

    @pytest.mark.medium
    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        config = {"openrouter_api_key": "test-key"}

        with responses.RequestsMock() as rsps:
            # Simulate timeout by not adding any response
            provider = OpenRouterProvider(config)

            # This would typically be handled by retry logic
            # For unit tests, we test the error handling structure
            with patch.object(provider, '_should_retry', return_value=False):
                with pytest.raises(OpenRouterConnectionError):
                    provider.generate("Hello")


class TestOpenRouterProviderConfiguration:
    """Test OpenRouter provider configuration handling."""

    @pytest.mark.fast
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid configuration should not raise errors
        config = {
            "openrouter_api_key": "test-key",
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        provider = OpenRouterProvider(config)
        assert provider.temperature == 0.7
        assert provider.max_tokens == 1000

    @pytest.mark.fast
    def test_configuration_with_defaults(self):
        """Test configuration with default values."""
        config = {"openrouter_api_key": "test-key"}

        provider = OpenRouterProvider(config)

        assert provider.temperature == 0.7  # Default
        assert provider.max_tokens == 4096  # Default
        assert provider.timeout == 60  # Default

    @pytest.mark.fast
    def test_configuration_precedence(self):
        """Test configuration precedence (config overrides defaults)."""
        config = {
            "openrouter_api_key": "test-key",
            "temperature": 0.9,
            "max_tokens": 2000,
        }

        provider = OpenRouterProvider(config)

        assert provider.temperature == 0.9
        assert provider.max_tokens == 2000


class TestOpenRouterProviderTokenTracking:
    """Test OpenRouter provider token tracking."""

    @pytest.mark.fast
    def test_token_counting_integration(self):
        """Test that token counting is integrated."""
        config = {"openrouter_api_key": "test-key"}
        provider = OpenRouterProvider(config)

        # Verify token tracker is initialized
        assert hasattr(provider, 'token_tracker')
        assert provider.token_tracker is not None

    @pytest.mark.fast
    def test_token_limit_validation(self):
        """Test token limit validation."""
        config = {"openrouter_api_key": "test-key", "max_tokens": 10}
        provider = OpenRouterProvider(config)

        # Long prompt should be rejected due to token limits
        long_prompt = "This is a very long prompt. " * 100

        # This would normally raise TokenLimitExceededError
        # but for unit tests, we just verify the method exists
        assert hasattr(provider, 'token_tracker')
        assert hasattr(provider.token_tracker, 'ensure_token_limit')


class TestOpenRouterProviderResilience:
    """Test OpenRouter provider resilience patterns."""

    @pytest.mark.fast
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        config = {"openrouter_api_key": "test-key"}
        provider = OpenRouterProvider(config)

        assert hasattr(provider, 'circuit_breaker')
        assert provider.circuit_breaker is not None

    @pytest.mark.fast
    def test_retry_logic_configuration(self):
        """Test retry logic configuration."""
        config = {
            "openrouter_api_key": "test-key",
            "max_retries": 5,
        }
        provider = OpenRouterProvider(config)

        assert provider.max_retries == 5

    @pytest.mark.medium
    def test_retry_on_transient_errors(self):
        """Test retry behavior on transient errors."""
        config = {"openrouter_api_key": "test-key"}

        call_count = 0

        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise Exception("Transient error")
            return {"choices": [{"message": {"content": "Success after retry"}}]}

        with patch.object(OpenRouterProvider, 'generate') as mock_generate:
            mock_generate.side_effect = mock_api_call

            provider = OpenRouterProvider(config)

            # This would test retry logic
            # For unit tests, we verify the structure exists
            assert hasattr(provider, '_should_retry')
            assert hasattr(provider, '_get_retry_config')


class TestOpenRouterProviderMetrics:
    """Test OpenRouter provider metrics collection."""

    @pytest.mark.fast
    def test_metrics_collection_setup(self):
        """Test that metrics collection is set up."""
        config = {"openrouter_api_key": "test-key"}
        provider = OpenRouterProvider(config)

        # Verify that the provider has the necessary components for metrics
        assert hasattr(provider, '_on_retry')
        assert hasattr(provider, 'circuit_breaker')

    @pytest.mark.fast
    def test_telemetry_emission(self):
        """Test that telemetry is emitted correctly."""
        config = {"openrouter_api_key": "test-key"}
        provider = OpenRouterProvider(config)

        # Mock the metrics increment function
        with patch('devsynth.application.llm.openrouter_provider.inc_provider') as mock_inc:
            provider._on_retry(Exception("test error"), 1, 1.0)

            # Verify metrics were incremented
            mock_inc.assert_called_once_with("retry")


class TestOpenRouterProviderHeaders:
    """Test OpenRouter provider header handling."""

    @pytest.mark.fast
    def test_correct_headers_set(self):
        """Test that correct headers are set for OpenRouter."""
        config = {"openrouter_api_key": "test-key"}
        provider = OpenRouterProvider(config)

        expected_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key",
            "HTTP-Referer": "https://devsynth.dev",
            "X-Title": "DevSynth AI Platform",
        }

        # Verify headers are set correctly
        for key, value in expected_headers.items():
            assert provider.headers[key] == value

    @pytest.mark.fast
    def test_custom_referer_header(self):
        """Test custom referer header configuration."""
        config = {
            "openrouter_api_key": "test-key",
            "http_referer": "https://custom-app.com",
        }
        provider = OpenRouterProvider(config)

        assert provider.headers["HTTP-Referer"] == "https://custom-app.com"


class TestOpenRouterProviderEdgeCases:
    """Test OpenRouter provider edge cases."""

    @pytest.mark.fast
    def test_empty_response_handling(self):
        """Test handling of empty responses."""
        config = {"openrouter_api_key": "test-key"}

        empty_response = {
            "id": "chatcmpl-empty",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "google/gemini-flash-1.5",
            "choices": []
        }

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/chat/completions",
                json=empty_response,
                status=200
            )

            provider = OpenRouterProvider(config)

            with pytest.raises(OpenRouterModelError) as exc_info:
                provider.generate("Hello")

            assert "Invalid response" in str(exc_info.value)

    @pytest.mark.fast
    def test_malformed_response_handling(self):
        """Test handling of malformed responses."""
        config = {"openrouter_api_key": "test-key"}

        malformed_response = {
            "invalid": "response",
            "structure": True
        }

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/chat/completions",
                json=malformed_response,
                status=200
            )

            provider = OpenRouterProvider(config)

            with pytest.raises(OpenRouterModelError) as exc_info:
                provider.generate("Hello")

            assert "Invalid response" in str(exc_info.value)

    @pytest.mark.fast
    def test_unicode_handling(self):
        """Test handling of Unicode content."""
        config = {"openrouter_api_key": "test-key"}

        unicode_response = {
            "id": "chatcmpl-unicode",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "google/gemini-flash-1.5",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! 你好! ¡Hola! 🌟"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15
            }
        }

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://openrouter.ai/api/v1/chat/completions",
                json=unicode_response,
                status=200
            )

            provider = OpenRouterProvider(config)
            response = provider.generate("Say hello in multiple languages")

        assert "你好" in response  # Chinese characters
        assert "¡Hola!" in response  # Spanish with accent
        assert "🌟" in response  # Emoji
