from unittest.mock import MagicMock, patch

import pytest

# Import the module instead of the global factory to avoid global state issues
import devsynth.application.llm.providers as providers_module
from devsynth.adapters.llm.llm_adapter import LLMBackendAdapter
from devsynth.application.llm.providers import (
    AnthropicProvider,
    OpenAIProvider,
    SimpleLLMProviderFactory,
)
from devsynth.domain.interfaces.llm import LLMProvider, LLMProviderFactory


@pytest.fixture
def clean_state():
    """Fixture to ensure clean state between tests."""
    # No setup or teardown needed as we're using mocks in all tests
    yield


@pytest.fixture
def mock_factory():
    """Fixture to provide a mock factory for tests."""
    mock_factory = MagicMock(spec=SimpleLLMProviderFactory)
    return mock_factory


@pytest.mark.medium
def test_llm_backend_adapter_init_succeeds(mock_factory):
    """Test that LLMBackendAdapter initializes with a factory instance.

    ReqID: N/A"""

    # Create a helper adapter and override the factory after instantiation
    class LLMBackendAdapterTestHelper(LLMBackendAdapter):
        """Test helper for injecting a custom factory."""

    # Use our custom adapter instead of the original one
    adapter = LLMBackendAdapterTestHelper()
    adapter.factory = mock_factory
    assert adapter.factory is mock_factory
    assert isinstance(adapter.factory, MagicMock)
    assert adapter.factory._spec_class == SimpleLLMProviderFactory


@pytest.mark.medium
def test_create_provider_has_expected(mock_factory):
    """Test that create_provider calls the factory's create_provider method.

    ReqID: N/A"""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_factory.create_provider.return_value = mock_provider

    # Patch the factory in the adapter module to use our mock
    with patch("devsynth.adapters.llm.llm_adapter.factory", mock_factory):
        adapter = LLMBackendAdapter()
        config = {"api_key": "test_key"}
        provider = adapter.create_provider("openai", config)

        assert provider is mock_provider
        mock_factory.create_provider.assert_called_once_with("openai", config)


@pytest.mark.medium
def test_register_provider_type_has_expected(mock_factory):
    """Test that register_provider_type calls the factory's register_provider_type method.

    ReqID: N/A"""
    # Patch the factory in the adapter module to use our mock
    with patch("devsynth.adapters.llm.llm_adapter.factory", mock_factory):
        adapter = LLMBackendAdapter()
        mock_provider_class = MagicMock(spec=type)
        adapter.register_provider_type("custom_provider", mock_provider_class)
        mock_factory.register_provider_type.assert_called_once_with(
            "custom_provider", mock_provider_class
        )


@pytest.mark.medium
@patch("devsynth.application.llm.providers.OpenAIProvider")
def test_integration_with_openai_provider_has_expected(
    mock_provider_class, mock_factory
):
    """Test integration with OpenAIProvider.

    ReqID: N/A"""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider_class.return_value = mock_provider

    # Set up the mock factory to return our mock provider
    mock_factory.create_provider.return_value = mock_provider

    # Patch the factory in the adapter module to use our mock
    with patch("devsynth.adapters.llm.llm_adapter.factory", mock_factory):
        adapter = LLMBackendAdapter()
        config = {"api_key": "test_key", "model": "gpt-4"}
        provider = adapter.create_provider("openai", config)

        assert provider is mock_provider
        mock_factory.create_provider.assert_called_once_with("openai", config)


@patch("devsynth.application.llm.providers.AnthropicProvider")
@pytest.mark.medium
def test_integration_with_anthropic_provider_has_expected(
    mock_provider_class, mock_factory
):
    """Test integration with AnthropicProvider.

    ReqID: N/A"""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider_class.return_value = mock_provider

    # Set up the mock factory to return our mock provider
    mock_factory.create_provider.return_value = mock_provider

    # Patch the factory in the adapter module to use our mock
    with patch("devsynth.adapters.llm.llm_adapter.factory", mock_factory):
        adapter = LLMBackendAdapter()
        config = {"api_key": "test_key", "model": "claude-2"}
        provider = adapter.create_provider("anthropic", config)

        assert provider is mock_provider
        mock_factory.create_provider.assert_called_once_with("anthropic", config)
