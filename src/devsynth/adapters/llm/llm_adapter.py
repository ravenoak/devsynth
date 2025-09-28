from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.llm import LLMProvider, LLMProviderFactory

# Create a logger for this module
logger = DevSynthLogger(__name__)


def _default_factory() -> LLMProviderFactory:
    """Resolve the globally registered provider factory lazily."""

    from ...application.llm import providers

    return providers.factory


@dataclass(slots=True)
class LLMProviderRequest:
    """Typed payload used when requesting a provider from the factory."""

    provider_type: str
    config: dict[str, Any] | None = None


@dataclass(slots=True)
class LLMBackendAdapter:
    """Adapter for LLM backends."""

    factory: LLMProviderFactory = field(default_factory=_default_factory)

    def create_provider(self, request: LLMProviderRequest) -> LLMProvider:
        """Create an LLM provider of the specified type."""
        return self.factory.create_provider(request.provider_type, request.config)

    def register_provider_type(
        self, provider_type: str, provider_class: type[LLMProvider]
    ) -> None:
        """Register a new provider type."""
        self.factory.register_provider_type(provider_type, provider_class)
