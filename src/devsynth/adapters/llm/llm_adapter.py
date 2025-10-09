from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, cast

from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.llm import LLMProvider

# Create a logger for this module
logger = DevSynthLogger(__name__)


class LLMProviderFactoryProtocol(Protocol):
    """Structural protocol for LLM provider factories."""

    def create_provider(
        self, provider_type: str, config: Mapping[str, object] | None = None
    ) -> LLMProvider:
        """Create a provider for the given type."""

    def register_provider_type(
        self, provider_type: str, provider_class: type[LLMProvider]
    ) -> None:
        """Register a provider implementation with the factory."""


def _default_factory() -> LLMProviderFactoryProtocol:
    """Resolve the globally registered provider factory lazily."""

    from ...application.llm import providers

    return cast(LLMProviderFactoryProtocol, providers.factory)


class UnknownLLMProviderError(Exception):
    """Raised when a requested provider type is not registered."""

    def __init__(self, provider_type: str, *, cause: Exception | None = None) -> None:
        message = f"LLM provider '{provider_type}' is not registered."
        super().__init__(message)
        self.provider_type = provider_type
        self.__cause__ = cause


@dataclass(slots=True, frozen=True)
class LLMProviderConfig:
    """Typed payload describing the provider request."""

    provider_type: str
    parameters: Mapping[str, object] | None = None

    def normalized_parameters(self) -> Mapping[str, object] | None:
        """Return a dictionary copy of the configuration if provided."""

        if self.parameters is None:
            return None
        return dict(self.parameters)


@dataclass(slots=True)
class LLMBackendAdapter:
    """Adapter for LLM backends."""

    factory: LLMProviderFactoryProtocol = field(default_factory=_default_factory)

    def create_provider(self, config: LLMProviderConfig) -> LLMProvider:
        """Create an LLM provider of the specified type."""

        normalized = config.normalized_parameters()
        try:
            return self.factory.create_provider(config.provider_type, normalized)
        except Exception as exc:
            message = getattr(exc, "message", str(exc)).lower()
            if "unknown provider" in message or "provider is not registered" in message:
                raise UnknownLLMProviderError(config.provider_type, cause=exc) from exc
            raise

    def register_provider_type(
        self, provider_type: str, provider_class: type[LLMProvider]
    ) -> None:
        """Register a new provider type."""
        self.factory.register_provider_type(provider_type, provider_class)
