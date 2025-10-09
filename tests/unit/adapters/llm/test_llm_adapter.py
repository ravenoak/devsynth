import sys
from types import MappingProxyType, ModuleType
from unittest.mock import ANY, MagicMock

import pytest

from devsynth.adapters.llm import llm_adapter
from devsynth.adapters.llm.llm_adapter import (
    LLMBackendAdapter,
    LLMProviderConfig,
    LLMProviderFactoryProtocol,
    UnknownLLMProviderError,
)
from devsynth.domain.interfaces.llm import LLMProvider


@pytest.fixture
def mock_factory() -> MagicMock:
    """Fixture to provide a mock factory for tests."""

    return MagicMock(spec=LLMProviderFactoryProtocol)


@pytest.mark.fast
def test_llm_provider_config_normalizes_mapping() -> None:
    """Ensure configuration payloads are normalized to dictionaries."""

    frozen_mapping = MappingProxyType({"api_key": "token"})
    config = LLMProviderConfig(provider_type="openai", parameters=frozen_mapping)

    normalized = config.normalized_parameters()

    assert normalized == {"api_key": "token"}
    assert normalized is not frozen_mapping


@pytest.mark.fast
def test_llm_provider_config_without_parameters_returns_none() -> None:
    """The config helper returns ``None`` when no parameters are provided."""

    config = LLMProviderConfig(provider_type="openai")

    assert config.normalized_parameters() is None


@pytest.mark.fast
def test_default_factory_delegates_to_global_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adapter resolves the application-level provider registry lazily."""

    sentinel_factory = MagicMock(spec=LLMProviderFactoryProtocol)
    providers_module = ModuleType("devsynth.application.llm.providers")
    providers_module.factory = sentinel_factory  # type: ignore[attr-defined]
    llm_module = ModuleType("devsynth.application.llm")
    llm_module.providers = providers_module  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "devsynth.application.llm", llm_module)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.llm.providers", providers_module
    )

    resolved = llm_adapter._default_factory()

    assert resolved is sentinel_factory


@pytest.mark.fast
def test_create_provider_uses_injected_factory(mock_factory: MagicMock) -> None:
    """The adapter delegates provider creation to the injected factory."""

    mock_provider = MagicMock(spec=LLMProvider)
    mock_factory.create_provider.return_value = mock_provider
    adapter = LLMBackendAdapter(factory=mock_factory)
    config = LLMProviderConfig("openai", {"model": "gpt-4"})

    provider = adapter.create_provider(config)

    assert provider is mock_provider
    mock_factory.create_provider.assert_called_once_with("openai", {"model": "gpt-4"})


@pytest.mark.fast
def test_create_provider_emits_typed_error_for_unknown_provider(
    mock_factory: MagicMock,
) -> None:
    """Translate unknown-provider failures into a typed adapter error."""

    mock_factory.create_provider.side_effect = ValueError("Unknown provider type: test")
    adapter = LLMBackendAdapter(factory=mock_factory)

    with pytest.raises(UnknownLLMProviderError) as exc_info:
        adapter.create_provider(LLMProviderConfig("test"))

    assert exc_info.value.provider_type == "test"
    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.fast
def test_create_provider_maps_registered_message(mock_factory: MagicMock) -> None:
    """Gracefully translate alternative unknown-provider messages."""

    mock_factory.create_provider.side_effect = ValueError(
        "Provider is not registered anywhere"
    )
    adapter = LLMBackendAdapter(factory=mock_factory)

    with pytest.raises(UnknownLLMProviderError):
        adapter.create_provider(LLMProviderConfig("ghost"))


@pytest.mark.fast
def test_register_provider_type_propagates_factory_rejection(
    mock_factory: MagicMock,
) -> None:
    """Surface registration failures raised by the factory."""

    mock_factory.register_provider_type.side_effect = RuntimeError("duplicate")
    adapter = LLMBackendAdapter(factory=mock_factory)

    with pytest.raises(RuntimeError, match="duplicate"):
        adapter.register_provider_type("custom", MagicMock(spec=type))


@pytest.mark.fast
def test_register_provider_type_success(mock_factory: MagicMock) -> None:
    """Register provider types through the injected factory when no error occurs."""

    adapter = LLMBackendAdapter(factory=mock_factory)

    adapter.register_provider_type("custom", MagicMock(spec=type))

    mock_factory.register_provider_type.assert_called_with("custom", ANY)


@pytest.mark.fast
def test_unknown_llm_provider_error_preserves_cause() -> None:
    """The typed exception records the provider name and original cause."""

    cause = RuntimeError("boom")

    error = UnknownLLMProviderError("missing", cause=cause)

    assert error.provider_type == "missing"
    assert error.__cause__ is cause
