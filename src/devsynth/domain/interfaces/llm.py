from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional, Protocol

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt."""
        ...

    @abstractmethod
    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> str:
        """Generate text from a prompt with conversation context."""
        ...

    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text."""
        ...


class StreamingLLMProvider(LLMProvider, Protocol):
    """Protocol for LLM providers that support streaming."""

    @abstractmethod
    async def generate_stream(
        self, prompt: str, parameters: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with streaming."""
        ...

    @abstractmethod
    async def generate_with_context_stream(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with conversation context with streaming."""
        ...


class LLMProviderFactory(Protocol):
    """Protocol for creating LLM providers."""

    @abstractmethod
    def create_provider(
        self, provider_type: str, config: Dict[str, Any] = None
    ) -> LLMProvider:
        """Create an LLM provider of the specified type."""
        ...

    @abstractmethod
    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        """Register a new provider type."""
        ...
