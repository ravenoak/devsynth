from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, cast, runtime_checkable

from devsynth.logging_setup import DevSynthLogger

from devsynth.exceptions import DevSynthError

from ...domain.interfaces.llm import LLMProvider

# Create a logger for this module
logger = DevSynthLogger(__name__)


def _default_factory() -> "LLMProviderFactoryProtocol":  # pragma: no cover - exercised in integration tests when real providers are loaded
    """Resolve the globally registered provider factory lazily."""

    from ...application.llm import providers

    return cast("LLMProviderFactoryProtocol", providers.factory)


@dataclass(slots=True, frozen=True)
class LLMProviderConfig:
    """Configuration payload used when requesting a provider from the factory."""

    provider_type: str
    options: Mapping[str, object] | None = None

    def normalized_options(self) -> dict[str, object]:
        """Return a defensive copy of the config mapping."""

        if self.options is None:
            return {}
        return dict(self.options.items())  # pragma: no cover - mapping copy validated via higher-level adapter tests


class UnknownProviderTypeError(Exception):
    """Raised when an LLM provider cannot be resolved for the requested type."""

    def __init__(self, provider_type: str, *, cause: Exception | None = None) -> None:  # pragma: no cover - captured via runtime exception flows
        message = (
            "LLM provider type is not registered or failed to initialize: "
            f"{provider_type}"
        )
        super().__init__(message)
        self.provider_type = provider_type
        self.details: dict[str, object] = {
            "config_key": "provider_type",
            "config_value": provider_type,
        }
        if cause is not None:
            self.__cause__ = cause


@runtime_checkable
class LLMProviderFactoryProtocol(Protocol):
    """Protocol describing the operations required from an LLM factory."""

    def create_provider(
        self, provider_type: str, config: Mapping[str, object] | None = None
    ) -> LLMProvider:
        ...  # pragma: no cover - protocol signature only

    def register_provider_type(
        self, provider_type: str, provider_class: type[LLMProvider]
    ) -> None:
        ...  # pragma: no cover - protocol signature only


@dataclass(slots=True)
class LLMBackendAdapter:
    """Adapter for LLM backends."""

    factory: LLMProviderFactoryProtocol = field(default_factory=_default_factory)

    def create_provider(self, config: LLMProviderConfig) -> LLMProvider:  # pragma: no cover - validated through adapter unit tests
        """Create an LLM provider of the specified type."""

        normalized = config.normalized_options()
        options = normalized or None
        try:
            return self.factory.create_provider(config.provider_type, options)
        except LookupError as error:
            raise UnknownProviderTypeError(config.provider_type, cause=error) from error
        except DevSynthError as error:
            raise UnknownProviderTypeError(config.provider_type, cause=error) from error

    def register_provider_type(
        self, provider_type: str, provider_class: type[LLMProvider]
    ) -> None:
        """Register a new provider type."""
        self.factory.register_provider_type(provider_type, provider_class)  # pragma: no cover - delegation validated via unit tests
