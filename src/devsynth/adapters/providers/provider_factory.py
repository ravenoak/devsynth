from __future__ import annotations

"""Provider factory with explicit provider selection rules."""

from typing import Any, Dict, Optional

from devsynth.adapters import provider_system

# Re-export commonly used symbols for convenience
ProviderType = provider_system.ProviderType
LMStudioProvider = provider_system.LMStudioProvider
OpenAIProvider = provider_system.OpenAIProvider
ProviderError = provider_system.ProviderError


class ProviderFactory(provider_system.ProviderFactory):
    """Factory class for creating provider instances with strict validation."""

    @staticmethod
    def create_provider(
        provider_type: str | None = None,
        *,
        config: dict[str, Any] | None = None,
        tls_config: provider_system.TLSConfig | None = None,
        retry_config: dict[str, Any] | None = None,
    ) -> provider_system.BaseProvider:
        """Create a provider instance.

        When ``provider_type`` explicitly requests OpenAI or Anthropic but no API key is
        configured, a :class:`ProviderError` is raised instead of falling back
        to another provider. This ensures that explicit provider selection does
        not silently degrade to a different backend.
        """
        if provider_type is not None:
            pt_value = (
                provider_type.value
                if isinstance(provider_type, ProviderType)
                else str(provider_type).lower()
            )
            cfg = config or provider_system.get_provider_config()
            if pt_value == ProviderType.OPENAI.value:
                if not cfg.get("openai", {}).get("api_key"):
                    raise ProviderError("OpenAI API key not found")
            if pt_value == ProviderType.ANTHROPIC.value:
                import os

                if not os.environ.get("ANTHROPIC_API_KEY"):
                    raise ProviderError("Anthropic API key not found")

        return provider_system.ProviderFactory.create_provider(
            provider_type,
            config=config,
            tls_config=tls_config,
            retry_config=retry_config,
        )
