from typing import Any, TypeAlias

from devsynth.exceptions import ValidationError

from ...domain.interfaces.memory import VectorStore, VectorStoreProviderFactory
from ...domain.models.memory import MemoryVector


VectorStoreRegistry: TypeAlias = dict[str, type[VectorStore[MemoryVector]]]


def _register_provider(
    registry: VectorStoreRegistry,
    provider_type: str,
    provider_class: type[VectorStore[MemoryVector]],
) -> None:
    if not provider_type:
        raise ValidationError("Provider type name must be provided.")
    if provider_type in registry:
        raise ValidationError(
            f"Vector store type '{provider_type}' is already registered."
        )
    registry[provider_type] = provider_class


def _lookup_provider(
    registry: VectorStoreRegistry, provider_type: str
) -> type[VectorStore[MemoryVector]]:
    try:
        return registry[provider_type]
    except KeyError as exc:
        available = ", ".join(sorted(registry)) or "none"
        raise ValidationError(
            "Unknown vector store type: "
            f"{provider_type}. Available types: {available}"
        ) from exc


class SimpleVectorStoreProviderFactory(VectorStoreProviderFactory[MemoryVector]):
    """Simple implementation of :class:`VectorStoreProviderFactory`."""

    def __init__(self) -> None:
        self.provider_types: VectorStoreRegistry = {}

    def create_provider(
        self, provider_type: str, config: dict[str, Any] | None = None
    ) -> VectorStore[MemoryVector]:
        provider_class = _lookup_provider(self.provider_types, provider_type)
        config = config or {}
        return provider_class(**config)

    def register_provider_type(
        self, provider_type: str, provider_class: type[VectorStore[MemoryVector]]
    ) -> None:
        _register_provider(self.provider_types, provider_type, provider_class)


factory = SimpleVectorStoreProviderFactory()

# Register built-in in-memory provider
from .adapters.vector_memory_adapter import VectorMemoryAdapter

factory.register_provider_type("in_memory", VectorMemoryAdapter)
