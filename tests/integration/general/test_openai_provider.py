import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import requests

from devsynth.application.llm.openai_provider import (
    OpenAIConnectionError,
    OpenAIModelError,
    OpenAIProvider,
)

openai_available = pytest.mark.requires_resource("openai")


class TestOpenAIProvider:
    """Tests for the OpenAIProvider class.

    ReqID: N/A"""

    def test_init_with_default_config_succeeds(self):
        """Test initialization with default configuration.

        ReqID: N/A"""
        with (
            patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
            patch(
                "devsynth.application.llm.openai_provider.AsyncOpenAI"
            ) as mock_async_openai,
        ):
            provider = OpenAIProvider({"openai_api_key": "test_key"})
            assert provider.model == "gpt-3.5-turbo"
            assert provider.max_tokens == 2000
            assert provider.temperature == 0.7
            assert provider.api_key == "test_key"

    def test_init_with_specified_model_succeeds(self):
        """Test initialization with a specified model.

        ReqID: N/A"""
        with (
            patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
            patch(
                "devsynth.application.llm.openai_provider.AsyncOpenAI"
            ) as mock_async_openai,
        ):
            provider = OpenAIProvider(
                {"openai_api_key": "test_key", "openai_model": "gpt-4"}
            )
            assert provider.model == "gpt-4"

    def test_init_without_api_key_succeeds(self):
        """Test initialization without an API key.

        ReqID: N/A"""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "devsynth.application.llm.openai_provider.get_llm_settings"
            ) as mock_settings,
        ):
            mock_settings.return_value = {
                "provider": "openai",
                "api_base": "",
                "model": "",
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": False,
                "openai_api_key": None,
                "openai_model": "gpt-3.5-turbo",
                "openai_embedding_model": "text-embedding-ada-002",
            }
            with pytest.raises(OpenAIConnectionError):
                OpenAIProvider({})

    def test_generate_with_connection_error_succeeds(self):
        """Test generating text when OpenAI is not available.

        ReqID: N/A"""
        with (
            patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
            patch(
                "devsynth.application.llm.openai_provider.AsyncOpenAI"
            ) as mock_async_openai,
        ):
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception(
                "Connection error"
            )
            mock_openai.return_value = mock_client
            provider = OpenAIProvider({"openai_api_key": "test_key"})
            with pytest.raises(OpenAIConnectionError):
                provider.generate("Hello, how are you?")

    def test_generate_with_context_succeeds(self):
        """Test generating text with context.

        ReqID: N/A"""
        with (
            patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
            patch(
                "devsynth.application.llm.openai_provider.AsyncOpenAI"
            ) as mock_async_openai,
        ):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "This is a test response"
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            provider = OpenAIProvider({"openai_api_key": "test_key"})
            context = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, who are you?"},
                {
                    "role": "assistant",
                    "content": "I'm an AI assistant. How can I help you?",
                },
            ]
            response = provider.generate_with_context(
                "Tell me more about yourself.", context
            )
            assert response == "This is a test response"
            messages_arg = mock_client.chat.completions.create.call_args[1]["messages"]
            assert len(messages_arg) == 4
            assert messages_arg[-1]["content"] == "Tell me more about yourself."

    def test_get_embedding_succeeds(self):
        """Test getting embeddings.

        ReqID: N/A"""
        with (
            patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
            patch(
                "devsynth.application.llm.openai_provider.AsyncOpenAI"
            ) as mock_async_openai,
        ):
            mock_response = MagicMock()
            mock_response.data = [MagicMock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3]
            mock_client = MagicMock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            provider = OpenAIProvider({"openai_api_key": "test_key"})
            embedding = provider.get_embedding("Test text")
            assert embedding == [0.1, 0.2, 0.3]

    @openai_available
    def test_generate_integration_succeeds(self):
        """Integration test for generating text from OpenAI.

        ReqID: N/A"""
        with (
            patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
            patch(
                "devsynth.application.llm.openai_provider.AsyncOpenAI"
            ) as mock_async_openai,
            patch(
                "devsynth.application.llm.openai_provider.get_llm_settings"
            ) as mock_settings,
        ):
            mock_settings.return_value = {
                "openai_api_key": "test_key",
                "openai_model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "api_base": None,
            }
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = (
                "This is a test response from the mocked OpenAI API"
            )
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            provider = OpenAIProvider({"openai_api_key": "test_key"})
            response = provider.generate("Hello, how are you?")
            assert isinstance(response, str)
            assert response == "This is a test response from the mocked OpenAI API"
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args[1]
            assert call_args["model"] == "gpt-3.5-turbo"
            assert call_args["messages"] == [
                {"role": "user", "content": "Hello, how are you?"}
            ]
            assert call_args["temperature"] == 0.7
            assert call_args["max_tokens"] == 2000

    @openai_available
    def test_generate_with_context_integration_succeeds(self):
        """Integration test for generating text with context from OpenAI.

        ReqID: N/A"""
        with (
            patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
            patch(
                "devsynth.application.llm.openai_provider.AsyncOpenAI"
            ) as mock_async_openai,
            patch(
                "devsynth.application.llm.openai_provider.get_llm_settings"
            ) as mock_settings,
        ):
            mock_settings.return_value = {
                "openai_api_key": "test_key",
                "openai_model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "api_base": None,
            }
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = (
                "This is a test response with context from the mocked OpenAI API"
            )
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            provider = OpenAIProvider({"openai_api_key": "test_key"})
            context = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, who are you?"},
                {
                    "role": "assistant",
                    "content": "I'm an AI assistant. How can I help you?",
                },
            ]
            response = provider.generate_with_context(
                "Tell me more about yourself.", context
            )
            assert isinstance(response, str)
            assert (
                response
                == "This is a test response with context from the mocked OpenAI API"
            )
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args[1]
            assert call_args["model"] == "gpt-3.5-turbo"
            messages_arg = call_args["messages"]
            assert len(messages_arg) == 4
            assert messages_arg[-1]["content"] == "Tell me more about yourself."
            assert call_args["temperature"] == 0.7
            assert call_args["max_tokens"] == 2000

    @openai_available
    def test_get_embedding_integration_succeeds(self):
        """Integration test for getting embeddings from OpenAI.

        ReqID: N/A"""
        with (
            patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
            patch(
                "devsynth.application.llm.openai_provider.AsyncOpenAI"
            ) as mock_async_openai,
            patch(
                "devsynth.application.llm.openai_provider.get_llm_settings"
            ) as mock_settings,
        ):
            mock_settings.return_value = {
                "openai_api_key": "test_key",
                "openai_model": "gpt-3.5-turbo",
                "openai_embedding_model": "text-embedding-ada-002",
                "max_tokens": 2000,
                "temperature": 0.7,
                "api_base": None,
            }
            mock_response = MagicMock()
            mock_response.data = [MagicMock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_client = MagicMock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            provider = OpenAIProvider({"openai_api_key": "test_key"})
            embedding = provider.get_embedding("Test text")
            assert isinstance(embedding, list)
            assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_client.embeddings.create.assert_called_once()
            call_args = mock_client.embeddings.create.call_args[1]
            assert call_args["model"] == "text-embedding-ada-002"
            assert call_args["input"] == "Test text"


if __name__ == "__main__":
    pytest.main(["-v", "test_openai_provider.py"])
