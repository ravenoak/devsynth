import os
import json
import pytest
import tempfile
import requests
from unittest.mock import patch, MagicMock

from devsynth.application.llm.lmstudio_provider import (
    LMStudioProvider, LMStudioConnectionError, LMStudioModelError
)

# Use the requires_resource marker for tests that need LM Studio
lmstudio_available = pytest.mark.requires_resource("lmstudio")

class TestLMStudioProvider:
    """Tests for the LMStudioProvider class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        with patch('devsynth.application.llm.lmstudio_provider.get_llm_settings') as mock_settings, \
             patch('devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models') as mock_list:

            # Mock the settings to return consistent values
            mock_settings.return_value = {
                "api_base": "http://localhost:1234/v1",
                "model": None,
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": True
            }

            # Mock the list_available_models method to return a sample model
            mock_list.return_value = [{"id": "test_model", "name": "Test Model"}]

            # Initialize provider with default config
            provider = LMStudioProvider()

            # Check that the model was auto-selected
            assert provider.model == "test_model"
            assert provider.api_base == "http://localhost:1234/v1"
            assert provider.max_tokens == 1024

    def test_init_with_specified_model(self):
        """Test initialization with a specified model."""
        # Initialize provider with a specified model
        provider = LMStudioProvider({"model": "specified_model"})

        # Check that the specified model was used
        assert provider.model == "specified_model"

    def test_init_with_connection_error(self):
        """Test initialization when LM Studio is not available."""
        with patch('devsynth.application.llm.lmstudio_provider.get_llm_settings') as mock_settings, \
             patch('devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models') as mock_list:

            # Mock the settings to return consistent values
            mock_settings.return_value = {
                "api_base": "http://localhost:1234/v1",
                "model": None,
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": True
            }

            # Mock the list_available_models method to raise a connection error
            mock_list.side_effect = LMStudioConnectionError("Connection error")

            # Initialize provider with default config
            provider = LMStudioProvider()

            # Check that the default model was used
            assert provider.model == "local_model"

    def test_list_available_models_error(self):
        """Test listing available models when the API call fails."""
        with patch('requests.get') as mock_get:
            # Mock the requests.get method to return an error
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_get.return_value = mock_response

            # Initialize provider
            provider = LMStudioProvider({"auto_select_model": False})

            # Check that listing models raises the expected error
            with pytest.raises(LMStudioConnectionError):
                provider.list_available_models()

    @lmstudio_available
    def test_list_available_models_integration(self):
        """Integration test for listing available models from LM Studio."""
        # Initialize provider
        provider = LMStudioProvider()

        # List available models
        models = provider.list_available_models()

        # Check that models were returned
        assert isinstance(models, list)
        if models:
            assert "id" in models[0]

    @lmstudio_available
    def test_generate_integration(self):
        """Integration test for generating text from LM Studio."""
        # Always use a mock for integration tests to avoid real API calls
        with patch('devsynth.application.llm.lmstudio_provider.get_llm_settings') as mock_settings, \
             patch('devsynth.application.llm.lmstudio_provider.requests.post') as mock_post, \
             patch('devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models') as mock_list:

            # Mock the settings to return consistent values
            mock_settings.return_value = {
                "api_base": "http://localhost:1234/v1",
                "model": "test_model",
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": False
            }

            # Mock the list_available_models method to return a sample model
            mock_list.return_value = [{"id": "test_model", "name": "Test Model"}]

            # Mock the requests.post response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "This is a test response from the mocked LM Studio API"
                        }
                    }
                ]
            }
            mock_post.return_value = mock_response

            # Initialize provider
            provider = LMStudioProvider()

            # Generate text
            response = provider.generate("Hello, how are you?")

            # Check that a response was returned
            assert isinstance(response, str)
            assert response == "This is a test response from the mocked LM Studio API"

            # Verify that the post method was called with the correct arguments
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:1234/v1/chat/completions"
            assert "Hello, how are you?" in call_args[1]["data"]

    def test_generate_with_connection_error(self):
        """Test generating text when LM Studio is not available."""
        with patch('requests.post') as mock_post:
            # Mock the requests.post method to raise a connection error
            mock_post.side_effect = requests.RequestException("Connection error")

            # Initialize provider
            provider = LMStudioProvider({"auto_select_model": False})

            # Check that generating text raises the expected error
            with pytest.raises(LMStudioConnectionError):
                provider.generate("Hello, how are you?")

    def test_generate_with_invalid_response(self):
        """Test generating text when LM Studio returns an invalid response."""
        with patch('requests.post') as mock_post:
            # Mock the requests.post method to return an invalid response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"invalid": "response"}
            mock_post.return_value = mock_response

            # Initialize provider
            provider = LMStudioProvider({"auto_select_model": False})

            # Check that generating text raises the expected error
            with pytest.raises(LMStudioModelError):
                provider.generate("Hello, how are you?")

    @lmstudio_available
    def test_generate_with_context_integration(self):
        """Integration test for generating text with context from LM Studio."""
        # Always use a mock for integration tests to avoid real API calls
        with patch('devsynth.application.llm.lmstudio_provider.get_llm_settings') as mock_settings, \
             patch('devsynth.application.llm.lmstudio_provider.requests.post') as mock_post, \
             patch('devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models') as mock_list:

            # Mock the settings to return consistent values
            mock_settings.return_value = {
                "api_base": "http://localhost:1234/v1",
                "model": "test_model",
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": False
            }

            # Mock the list_available_models method to return a sample model
            mock_list.return_value = [{"id": "test_model", "name": "Test Model"}]

            # Mock the requests.post response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "This is a test response with context from the mocked LM Studio API"
                        }
                    }
                ]
            }
            mock_post.return_value = mock_response

            # Initialize provider
            provider = LMStudioProvider()

            # Generate text with context
            context = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, who are you?"},
                {"role": "assistant", "content": "I'm an AI assistant. How can I help you?"}
            ]
            response = provider.generate_with_context("Tell me more about yourself.", context)

            # Check that a response was returned
            assert isinstance(response, str)
            assert response == "This is a test response with context from the mocked LM Studio API"

            # Verify that the post method was called with the correct arguments
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:1234/v1/chat/completions"

            # Verify that the context was included in the API call
            data = json.loads(call_args[1]["data"])
            assert len(data["messages"]) == 4  # 3 context messages + 1 new message
            assert data["messages"][-1]["content"] == "Tell me more about yourself."

if __name__ == "__main__":
    pytest.main(["-v", "test_lmstudio_provider.py"])
