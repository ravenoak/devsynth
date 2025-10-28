from __future__ import annotations

from typing import Any
from collections.abc import AsyncGenerator

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ..domain.interfaces.llm import (
    LLMProvider,
    LLMProviderFactory,
    StreamingLLMProvider,
)

logger = DevSynthLogger(__name__)

from devsynth.exceptions import DevSynthError


class ValidationError(DevSynthError):
    """Exception raised when validation fails."""

    pass


class LLMPort:
    """Port for the LLM backend abstraction."""

    def __init__(self, provider_factory: LLMProviderFactory):
        self.provider_factory = provider_factory
        self.default_provider: LLMProvider | None = None

    def set_default_provider(
        self, provider_type: str, config: dict[str, Any] | None = None
    ) -> None:
        """Set the default LLM provider."""
        self.default_provider = self.provider_factory.create_provider(
            provider_type, config
        )

    def generate(
        self,
        prompt: str,
        parameters: dict[str, Any] | None = None,
        provider_type: str | None = None,
    ) -> str:
        """Generate text from a prompt."""
        provider = self._get_provider(provider_type)
        return provider.generate(prompt, parameters)

    def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] | None = None,
        provider_type: str | None = None,
    ) -> str:
        """Generate text from a prompt with conversation context."""
        provider = self._get_provider(provider_type)
        return provider.generate_with_context(prompt, context, parameters)

    def get_embedding(self, text: str, provider_type: str | None = None) -> list[float]:
        """Get an embedding vector for the given text."""
        provider = self._get_provider(provider_type)
        return provider.get_embedding(text)

    async def generate_stream(
        self,
        prompt: str,
        parameters: dict[str, Any] | None = None,
        provider_type: str | None = None,
    ) -> AsyncGenerator[str]:
        """Generate text from a prompt with streaming."""
        provider = self._get_provider(provider_type)
        if not isinstance(provider, StreamingLLMProvider):
            raise ValidationError(
                f"Provider {provider_type or 'default'} does not support streaming"
            )

        stream = await provider.generate_stream(prompt, parameters)
        async for chunk in stream:
            yield chunk

    async def generate_with_context_stream(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] | None = None,
        provider_type: str | None = None,
    ) -> AsyncGenerator[str]:
        """Generate text from a prompt with conversation context with streaming."""
        provider = self._get_provider(provider_type)
        if not isinstance(provider, StreamingLLMProvider):
            raise ValidationError(
                f"Provider {provider_type or 'default'} does not support streaming"
            )

        stream = await provider.generate_with_context_stream(
            prompt, context, parameters
        )
        async for chunk in stream:
            yield chunk

    def _get_provider(self, provider_type: str | None = None) -> LLMProvider:
        """Get the specified provider or the default one."""
        if provider_type:
            return self.provider_factory.create_provider(provider_type)
        if not self.default_provider:
            raise ValidationError(f"No default provider set")
        return self.default_provider
