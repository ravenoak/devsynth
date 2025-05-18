
import os
import pytest
import tempfile
import requests
from unittest.mock import patch, MagicMock

from devsynth.application.llm.openai_provider import (
    OpenAIProvider, OpenAIConnectionError, OpenAIModelError
)

# Use the requires_resource marker for tests that need OpenAI API
openai_available = pytest.mark.requires_resource("openai")

class TestOpenAIProvider:
    """Tests for the OpenAIProvider class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        with patch('devsynth.application.llm.openai_provider.OpenAI') as mock_openai, \
             patch('devsynth.application.llm.openai_provider.AsyncOpenAI') as mock_async_openai:
            # Initialize provider with default config
            provider = OpenAIProvider({
                "openai_api_key": "test_key"  # Required for initialization
            })

            # Check default values
            assert provider.model == "gpt-3.5-turbo"
            assert provider.max_tokens == 1024
            assert provider.temperature == 0.7
            assert provider.api_key == "test_key"

    def test_init_with_specified_model(self):
        """Test initialization with a specified model."""
        with patch('devsynth.application.llm.openai_provider.OpenAI') as mock_openai, \
             patch('devsynth.application.llm.openai_provider.AsyncOpenAI') as mock_async_openai:
            # Initialize provider with a specified model
            provider = OpenAIProvider({
                "openai_api_key": "test_key",
                "openai_model": "gpt-4"
            })

            # Check that the specified model was used
            assert provider.model == "gpt-4"

    def test_init_without_api_key(self):
        """Test initialization without an API key."""
        # Create a provider with empty config and no environment variables
        with patch.dict(os.environ, {}, clear=True), \
             patch('devsynth.application.llm.openai_provider.get_llm_settings') as mock_settings:
            # Mock settings to return empty API key
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
            
            # Check that initialization without an API key raises an error
            with pytest.raises(OpenAIConnectionError):
                OpenAIProvider({})

    def test_generate_with_connection_error(self):
        """Test generating text when OpenAI is not available."""
        with patch('devsynth.application.llm.openai_provider.OpenAI') as mock_openai, \
             patch('devsynth.application.llm.openai_provider.AsyncOpenAI') as mock_async_openai:
            # Mock the OpenAI client to raise an exception
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("Connection error")
            mock_openai.return_value = mock_client

            # Initialize provider
            provider = OpenAIProvider({
                "openai_api_key": "test_key"
            })

            # Check that generating text raises the expected error
            with pytest.raises(OpenAIConnectionError):
                provider.generate("Hello, how are you?")

    def test_generate_with_context(self):
        """Test generating text with context."""
        with patch('devsynth.application.llm.openai_provider.OpenAI') as mock_openai, \
             patch('devsynth.application.llm.openai_provider.AsyncOpenAI') as mock_async_openai:
            # Mock the OpenAI client response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "This is a test response"
            
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            # Initialize provider
            provider = OpenAIProvider({
                "openai_api_key": "test_key"
            })

            # Generate text with context
            context = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, who are you?"},
                {"role": "assistant", "content": "I'm an AI assistant. How can I help you?"}
            ]
            response = provider.generate_with_context("Tell me more about yourself.", context)

            # Check that the response matches the mock
            assert response == "This is a test response"
            
            # Check that the context was included in the API call
            messages_arg = mock_client.chat.completions.create.call_args[1]["messages"]
            assert len(messages_arg) == 4  # 3 context messages + 1 new message
            assert messages_arg[-1]["content"] == "Tell me more about yourself."

    def test_get_embedding(self):
        """Test getting embeddings."""
        with patch('devsynth.application.llm.openai_provider.OpenAI') as mock_openai, \
             patch('devsynth.application.llm.openai_provider.AsyncOpenAI') as mock_async_openai:
            # Mock the OpenAI client response
            mock_response = MagicMock()
            mock_response.data = [MagicMock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3]
            
            mock_client = MagicMock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client

            # Initialize provider
            provider = OpenAIProvider({
                "openai_api_key": "test_key"
            })

            # Get embedding
            embedding = provider.get_embedding("Test text")

            # Check that the embedding matches the mock
            assert embedding == [0.1, 0.2, 0.3]

    @openai_available
    def test_generate_integration(self):
        """Integration test for generating text from OpenAI."""
        # Skip if no API key is available
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("No OpenAI API key available")

        # Initialize provider
        provider = OpenAIProvider()

        # Generate text
        response = provider.generate("Hello, how are you?")

        # Check that a response was returned
        assert isinstance(response, str)
        assert len(response) > 0

    @openai_available
    def test_generate_with_context_integration(self):
        """Integration test for generating text with context from OpenAI."""
        # Skip if no API key is available
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("No OpenAI API key available")

        # Initialize provider
        provider = OpenAIProvider()

        # Generate text with context
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, who are you?"},
            {"role": "assistant", "content": "I'm an AI assistant. How can I help you?"}
        ]
        response = provider.generate_with_context("Tell me more about yourself.", context)

        # Check that a response was returned
        assert isinstance(response, str)
        assert len(response) > 0

    @openai_available
    def test_get_embedding_integration(self):
        """Integration test for getting embeddings from OpenAI."""
        # Skip if no API key is available
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("No OpenAI API key available")

        # Initialize provider
        provider = OpenAIProvider()

        # Get embedding
        embedding = provider.get_embedding("Test text")

        # Check that an embedding was returned
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

if __name__ == "__main__":
    pytest.main(["-v", "test_openai_provider.py"])
