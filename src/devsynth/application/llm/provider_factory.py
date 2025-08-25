"""Deterministic LLM provider factory."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .providers import (
    AnthropicProvider,
    LocalProvider,
    OfflineProvider,
    OpenAIProvider,
    SimpleLLMProviderFactory,
    ValidationError,
)

lmstudio_requested = os.getenv(
    "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false"
).lower() in {"1", "true", "yes"}
if lmstudio_requested:  # pragma: no cover - optional dependency
    try:
        from .lmstudio_provider import LMStudioProvider
    except ImportError:  # pragma: no cover - fallback path
        LMStudioProvider = None
else:  # pragma: no cover - optional dependency
    LMStudioProvider = None


class ProviderFactory(SimpleLLMProviderFactory):
    """Factory that selects providers in a deterministic order.

    Safe-by-default: prefer offline/local providers for implicit selection.
    """

    _order = ("offline", "local", "openai", "anthropic", "lmstudio")

    def create_provider(
        self,
        provider_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Create a provider instance.

        When ``provider_type`` is ``None``, providers are selected in the
        order defined by :attr:`_order` falling back to the alphabetically
        first registered provider.
        """

        if provider_type:
            return super().create_provider(provider_type.lower(), config)

        for name in self._order:
            if name in self.provider_types:
                return super().create_provider(name, config)

        if not self.provider_types:
            raise ValidationError("No providers registered")

        first = next(iter(sorted(self.provider_types)))
        return super().create_provider(first, config)


factory = ProviderFactory()
factory.register_provider_type("openai", OpenAIProvider)
factory.register_provider_type("anthropic", AnthropicProvider)
if LMStudioProvider is not None:  # pragma: no cover - optional dependency
    factory.register_provider_type("lmstudio", LMStudioProvider)
factory.register_provider_type("local", LocalProvider)
factory.register_provider_type("offline", OfflineProvider)
