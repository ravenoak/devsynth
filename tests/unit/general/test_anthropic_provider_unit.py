"""
Anthropic Provider Unit Tests

NOTE: Currently waiting on valid Anthropic API key for testing.
Tests requiring Anthropic API are expected to fail until key is available.

For tests requiring live LLM functionality, use OpenRouter free-tier instead.
"""

import unittest
from unittest.mock import MagicMock, patch

import httpx
import pytest

from devsynth.application.llm.providers import (
    AnthropicConnectionError,
    AnthropicModelError,
    AnthropicProvider,
)


class TestAnthropicProvider(unittest.TestCase):
    """Unit tests for AnthropicProvider.

    ReqID: N/A"""

    def setUp(self):
        self.provider = AnthropicProvider({"api_key": "test_key"})

    @pytest.mark.fast
    @patch("devsynth.application.llm.providers.httpx.post")
    def test_generate_succeeds(self, mock_post):
        """Test that generate succeeds.

        ReqID: N/A"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"content": [{"text": "hello"}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        result = self.provider.generate("hi")
        self.assertEqual(result, "hello")
        mock_post.assert_called_once()
        self.assertIn("/v1/messages", mock_post.call_args[0][0])
        self.assertEqual(mock_post.call_args[1]["headers"]["x-api-key"], "test_key")

    @pytest.mark.fast
    @patch("devsynth.application.llm.providers.httpx.post")
    def test_generate_with_context_succeeds(self, mock_post):
        """Test that generate with context.

        ReqID: N/A"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"content": [{"text": "context"}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        context = [{"role": "system", "content": "ok"}]
        result = self.provider.generate_with_context("prompt", context)
        self.assertEqual(result, "context")
        mock_post.assert_called_once()
        messages = mock_post.call_args[1]["json"]["messages"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[-1]["content"], "prompt")

    @pytest.mark.fast
    @patch("httpx.post")
    def test_get_embedding_succeeds(self, mock_post):
        """Test that get embedding.

        ReqID: N/A"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        embedding = self.provider.get_embedding("text")
        self.assertEqual(embedding, [0.1, 0.2])
        mock_post.assert_called_once()
        self.assertIn("/v1/embeddings", mock_post.call_args[0][0])

    @pytest.mark.fast
    @patch("devsynth.application.llm.providers.httpx.post")
    def test_connection_error_raises_error(self, mock_post):
        """Test that connection error.

        ReqID: N/A"""
        mock_post.side_effect = httpx.RequestError("boom", request=MagicMock())
        with self.assertRaises(AnthropicConnectionError):
            self.provider.generate("fail")

    @pytest.mark.fast
    @patch("devsynth.application.llm.providers.httpx.post")
    @patch("devsynth.fallback.time.sleep")
    def test_model_error_raises_error(self, mock_sleep, mock_post):
        """Test that model error.

        ReqID: N/A"""
        # Mock sleep to prevent actual delays during test
        mock_sleep.return_value = None

        # Disable circuit breaker for this test by setting a high failure threshold
        original_cb = self.provider.circuit_breaker
        self.provider.circuit_breaker = MagicMock()
        self.provider.circuit_breaker.call.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

        try:
            response = MagicMock()
            response.text = "server error"
            request = httpx.Request("POST", "http://test")
            mock_post.return_value = response
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "bad", request=request, response=httpx.Response(500, request=request)
            )
            with self.assertRaises(AnthropicConnectionError):
                self.provider.generate("bad")
        finally:
            # Restore original circuit breaker
            self.provider.circuit_breaker = original_cb


if __name__ == "__main__":
    unittest.main()
