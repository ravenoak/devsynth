from dataclasses import asdict
from unittest.mock import MagicMock

import pytest

from devsynth.adapters.llm.llm_adapter import LLMBackendAdapter, LLMProviderRequest
from devsynth.domain.interfaces.llm import LLMProvider, LLMProviderFactory
from devsynth.exceptions import ValidationError


@pytest.fixture
def mock_factory() -> MagicMock:
    """Fixture to provide a mock factory for tests."""

    return MagicMock(spec=LLMProviderFactory)


@pytest.mark.medium
def test_llm_provider_request_asdict_serializes_payload() -> None:
    """Ensure the provider request dataclass has predictable serialization."""

    request = LLMProviderRequest(provider_type="openai", config={"api_key": "token"})

    assert asdict(request) == {
        "provider_type": "openai",
        "config": {"api_key": "token"},
    }


@pytest.mark.medium
def test_create_provider_uses_injected_factory(mock_factory: MagicMock) -> None:
    """The adapter delegates provider creation to the injected factory."""

    mock_provider = MagicMock(spec=LLMProvider)
    mock_factory.create_provider.return_value = mock_provider
    adapter = LLMBackendAdapter(factory=mock_factory)
    request = LLMProviderRequest("openai", {"model": "gpt-4"})

    provider = adapter.create_provider(request)

    assert provider is mock_provider
    mock_factory.create_provider.assert_called_once_with("openai", {"model": "gpt-4"})


@pytest.mark.medium
def test_create_provider_propagates_validation_error(mock_factory: MagicMock) -> None:
    """Surface validation failures raised by the underlying factory."""

    mock_factory.create_provider.side_effect = ValidationError("boom")
    adapter = LLMBackendAdapter(factory=mock_factory)

    with pytest.raises(ValidationError, match="boom"):
        adapter.create_provider(LLMProviderRequest("missing"))


@pytest.mark.medium
def test_register_provider_type_delegates(mock_factory: MagicMock) -> None:
    """Register provider types through the injected factory."""

    adapter = LLMBackendAdapter(factory=mock_factory)
    provider_cls = MagicMock(spec=type)

    adapter.register_provider_type("custom", provider_cls)

    mock_factory.register_provider_type.assert_called_once_with("custom", provider_cls)
