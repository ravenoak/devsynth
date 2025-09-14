from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Protocol

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, parameters: dict[str, Any] | None = None) -> str:
        """Generate text from a prompt."""
        ...

    @abstractmethod
    def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Generate text from a prompt with conversation context."""
        ...

    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        """Get an embedding vector for the given text."""
        ...


class StreamingLLMProvider(LLMProvider, Protocol):
    """Protocol for LLM providers that support streaming."""

    @abstractmethod
    async def generate_stream(
        self, prompt: str, parameters: dict[str, Any] | None = None
    ) -> AsyncGenerator[str]:
        """Generate text from a prompt with streaming."""
        ...

    @abstractmethod
    async def generate_with_context_stream(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str]:
        """Generate text from a prompt with conversation context with streaming."""
        ...


class LLMProviderFactory(Protocol):
    """Protocol for creating LLM providers."""

    @abstractmethod
    def create_provider(
        self, provider_type: str, config: dict[str, Any] | None = None
    ) -> LLMProvider:
        """Create an LLM provider of the specified type."""
        ...

    @abstractmethod
    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        """Register a new provider type."""
        ...
