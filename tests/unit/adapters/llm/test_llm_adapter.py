import pytest
from unittest.mock import MagicMock, patch

from devsynth.adapters.llm.llm_adapter import LLMBackendAdapter
from devsynth.domain.interfaces.llm import LLMProvider, LLMProviderFactory
from devsynth.application.llm.providers import SimpleLLMProviderFactory, OpenAIProvider, AnthropicProvider


def test_llm_backend_adapter_init():
    """Test that LLMBackendAdapter initializes with a SimpleLLMProviderFactory."""
    adapter = LLMBackendAdapter()
    assert isinstance(adapter.factory, SimpleLLMProviderFactory)


@patch("devsynth.adapters.llm.llm_adapter.SimpleLLMProviderFactory")
def test_create_provider(mock_factory_class):
    """Test that create_provider calls the factory's create_provider method."""
    # Setup
    mock_factory = MagicMock()
    mock_factory_class.return_value = mock_factory
    mock_provider = MagicMock(spec=LLMProvider)
    mock_factory.create_provider.return_value = mock_provider
    
    # Execute
    adapter = LLMBackendAdapter()
    config = {"api_key": "test_key"}
    provider = adapter.create_provider("openai", config)
    
    # Verify
    assert provider is mock_provider
    mock_factory.create_provider.assert_called_once_with("openai", config)


@patch("devsynth.adapters.llm.llm_adapter.SimpleLLMProviderFactory")
def test_register_provider_type(mock_factory_class):
    """Test that register_provider_type calls the factory's register_provider_type method."""
    # Setup
    mock_factory = MagicMock()
    mock_factory_class.return_value = mock_factory
    
    # Execute
    adapter = LLMBackendAdapter()
    mock_provider_class = MagicMock(spec=type)
    adapter.register_provider_type("custom_provider", mock_provider_class)
    
    # Verify
    mock_factory.register_provider_type.assert_called_once_with("custom_provider", mock_provider_class)


def test_integration_with_openai_provider():
    """Test integration with OpenAIProvider."""
    # This test verifies that the adapter can create an OpenAIProvider
    adapter = LLMBackendAdapter()
    
    # Mock the OpenAIProvider to avoid actual API calls
    with patch("devsynth.application.llm.providers.OpenAIProvider") as mock_provider_class:
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider_class.return_value = mock_provider
        
        # Create an OpenAI provider
        config = {"api_key": "test_key", "model": "gpt-4"}
        provider = adapter.create_provider("openai", config)
        
        # Verify
        assert provider is mock_provider
        mock_provider_class.assert_called_once_with(api_key="test_key", model="gpt-4")


def test_integration_with_anthropic_provider():
    """Test integration with AnthropicProvider."""
    # This test verifies that the adapter can create an AnthropicProvider
    adapter = LLMBackendAdapter()
    
    # Mock the AnthropicProvider to avoid actual API calls
    with patch("devsynth.application.llm.providers.AnthropicProvider") as mock_provider_class:
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider_class.return_value = mock_provider
        
        # Create an Anthropic provider
        config = {"api_key": "test_key", "model": "claude-2"}
        provider = adapter.create_provider("anthropic", config)
        
        # Verify
        assert provider is mock_provider
        mock_provider_class.assert_called_once_with(api_key="test_key", model="claude-2")