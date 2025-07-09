import pytest
from unittest.mock import MagicMock, patch
from devsynth.adapters.llm.llm_adapter import LLMBackendAdapter
from devsynth.domain.interfaces.llm import LLMProvider, LLMProviderFactory
from devsynth.application.llm.providers import factory, SimpleLLMProviderFactory, OpenAIProvider, AnthropicProvider


def test_llm_backend_adapter_init_succeeds():
    """Test that LLMBackendAdapter initializes with the global factory instance.

ReqID: N/A"""
    adapter = LLMBackendAdapter()
    assert adapter.factory is factory
    assert isinstance(adapter.factory, SimpleLLMProviderFactory)


@patch('devsynth.application.llm.providers.factory.create_provider')
def test_create_provider_has_expected(mock_create_provider):
    """Test that create_provider calls the factory's create_provider method.

ReqID: N/A"""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_create_provider.return_value = mock_provider
    adapter = LLMBackendAdapter()
    config = {'api_key': 'test_key'}
    provider = adapter.create_provider('openai', config)
    assert provider is mock_provider
    mock_create_provider.assert_called_once_with('openai', config)


@patch('devsynth.application.llm.providers.factory.register_provider_type')
def test_register_provider_type_has_expected(mock_register_provider_type):
    """Test that register_provider_type calls the factory's register_provider_type method.

ReqID: N/A"""
    adapter = LLMBackendAdapter()
    mock_provider_class = MagicMock(spec=type)
    adapter.register_provider_type('custom_provider', mock_provider_class)
    mock_register_provider_type.assert_called_once_with('custom_provider',
        mock_provider_class)


@patch('devsynth.application.llm.providers.OpenAIProvider')
def test_integration_with_openai_provider_has_expected(mock_provider_class):
    """Test integration with OpenAIProvider.

ReqID: N/A"""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider_class.return_value = mock_provider
    adapter = LLMBackendAdapter()
    config = {'api_key': 'test_key', 'model': 'gpt-4'}
    with patch('devsynth.application.llm.providers.factory.create_provider'
        ) as mock_create_provider:
        mock_create_provider.return_value = mock_provider
        provider = adapter.create_provider('openai', config)
        assert provider is mock_provider
        mock_create_provider.assert_called_once_with('openai', config)


@patch('devsynth.application.llm.providers.AnthropicProvider')
def test_integration_with_anthropic_provider_has_expected(mock_provider_class):
    """Test integration with AnthropicProvider.

ReqID: N/A"""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider_class.return_value = mock_provider
    adapter = LLMBackendAdapter()
    config = {'api_key': 'test_key', 'model': 'claude-2'}
    with patch('devsynth.application.llm.providers.factory.create_provider'
        ) as mock_create_provider:
        mock_create_provider.return_value = mock_provider
        provider = adapter.create_provider('anthropic', config)
        assert provider is mock_provider
        mock_create_provider.assert_called_once_with('anthropic', config)
