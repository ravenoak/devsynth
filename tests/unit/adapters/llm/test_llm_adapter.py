import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from devsynth.adapters.llm.llm_adapter import (
    LLMBackendAdapter,
    LLMProviderConfig,
    LLMProviderFactoryProtocol,
    UnknownProviderTypeError,
)
from devsynth.domain.interfaces.llm import LLMProvider
from devsynth.exceptions import ConfigurationError


@pytest.fixture
def mock_factory() -> MagicMock:
    """Provide a protocol-backed factory double for tests."""

    return MagicMock(spec=LLMProviderFactoryProtocol)


@pytest.mark.fast
def test_llm_provider_config_normalizes_missing_options() -> None:
    """Default to an empty mapping when options are not supplied."""

    config = LLMProviderConfig(provider_type="openai")

    assert config.normalized_options() == {}


@pytest.mark.fast
def test_llm_provider_config_normalizes_to_copy() -> None:
    """Creating providers never mutates the caller-supplied mapping."""

    original = {"model": "gpt-4"}
    config = LLMProviderConfig(provider_type="openai", options=original)

    normalized = config.normalized_options()

    assert normalized == {"model": "gpt-4"}
    assert normalized is not original


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
def test_create_provider_omits_empty_options(mock_factory: MagicMock) -> None:
    """Explicitly pass ``None`` when no options are supplied."""

    adapter = LLMBackendAdapter(factory=mock_factory)

    with pytest.raises(UnknownProviderTypeError):
        # Trigger our LookupError path to avoid depending on real providers.
        mock_factory.create_provider.side_effect = LookupError
        adapter.create_provider(LLMProviderConfig("unregistered"))

    mock_factory.create_provider.assert_called_once_with("unregistered", None)


@pytest.mark.fast
def test_create_provider_wraps_devsynthexceptions(mock_factory: MagicMock) -> None:
    """Surface unknown-provider failures with a typed adapter exception."""

    mock_factory.create_provider.side_effect = ConfigurationError(
        "boom", config_key="provider_type", config_value="missing"
    )
    adapter = LLMBackendAdapter(factory=mock_factory)

    with pytest.raises(UnknownProviderTypeError) as exc_info:
        adapter.create_provider(LLMProviderConfig("missing"))

    assert exc_info.value.details["config_value"] == "missing"


@pytest.mark.fast
def test_register_provider_type_delegates(mock_factory: MagicMock) -> None:
    """Register provider types through the injected factory."""

    adapter = LLMBackendAdapter(factory=mock_factory)
    provider_cls = MagicMock(spec=type)

    adapter.register_provider_type("custom", provider_cls)

    mock_factory.register_provider_type.assert_called_once_with("custom", provider_cls)


@pytest.mark.fast
def test_register_provider_type_propagates_factory_failure(
    mock_factory: MagicMock,
) -> None:
    """Ensure registration rejections surface to callers."""

    adapter = LLMBackendAdapter(factory=mock_factory)
    mock_factory.register_provider_type.side_effect = RuntimeError("nope")

    with pytest.raises(RuntimeError, match="nope"):
        adapter.register_provider_type("broken", MagicMock(spec=type))


@pytest.mark.fast
def test_backend_adapter_lazy_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Instantiating without a factory resolves the providers module lazily."""

    stub_factory = MagicMock(spec=LLMProviderFactoryProtocol)
    providers_module = SimpleNamespace(factory=stub_factory)
    llm_package = SimpleNamespace(providers=providers_module)
    monkeypatch.setitem(sys.modules, "devsynth.application.llm.providers", providers_module)
    monkeypatch.setitem(sys.modules, "devsynth.application.llm", llm_package)

    adapter = LLMBackendAdapter()

    assert adapter.factory is stub_factory


@pytest.mark.fast
def test_unknown_provider_type_error_records_cause() -> None:
    """Expose provider metadata on the raised exception for callers."""

    cause = LookupError("missing")
    error = UnknownProviderTypeError("ghost", cause=cause)

    assert error.provider_type == "ghost"
    assert error.details["config_key"] == "provider_type"
    assert error.__cause__ is cause
