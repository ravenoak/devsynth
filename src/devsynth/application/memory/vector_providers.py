from typing import Any, Dict

from devsynth.exceptions import ValidationError

from ...domain.interfaces.memory import VectorStore, VectorStoreProviderFactory


class SimpleVectorStoreProviderFactory(VectorStoreProviderFactory):
    """Simple implementation of :class:`VectorStoreProviderFactory`."""

    def __init__(self) -> None:
        self.provider_types: Dict[str, type] = {}

    def create_provider(
        self, provider_type: str, config: Dict[str, Any] | None = None
    ) -> VectorStore:
        if provider_type not in self.provider_types:
            raise ValidationError(f"Unknown vector store type: {provider_type}")
        provider_class = self.provider_types[provider_type]
        config = config or {}
        return provider_class(**config)

    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        self.provider_types[provider_type] = provider_class


factory = SimpleVectorStoreProviderFactory()

# Register built-in in-memory provider
from .adapters.vector_memory_adapter import VectorMemoryAdapter

factory.register_provider_type("in_memory", VectorMemoryAdapter)
