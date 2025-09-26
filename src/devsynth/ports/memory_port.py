from __future__ import annotations

from typing import Any

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import inc_memory

from ..domain.interfaces.memory import ContextManager, MemoryStore
from ..domain.models.memory import MemoryItem, MemoryType

logger = DevSynthLogger(__name__)


class MemoryPort:
    """Port for the memory and context system, using Kuzu as the default backend."""

    def __init__(
        self,
        context_manager: ContextManager,
        memory_store: MemoryStore | None = None,
    ):
        # Use KuzuMemoryStore by default, but allow override for testing/extensibility
        if memory_store is None:
            # Lazy import to avoid circular dependency
            from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore

            memory_store = KuzuMemoryStore()
        self.memory_store = memory_store
        self.context_manager = context_manager

    def store_memory(
        self,
        content: Any,
        memory_type: MemoryType,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store an item in memory and return its ID."""
        item = MemoryItem(
            id="", content=content, memory_type=memory_type, metadata=metadata
        )
        inc_memory("store")
        return self.memory_store.store(item)

    def retrieve_memory(self, item_id: str) -> MemoryItem | None:
        """Retrieve an item from memory by ID."""
        inc_memory("retrieve")
        return self.memory_store.retrieve(item_id)

    def search_memory(self, query: dict[str, Any]) -> list[MemoryItem]:
        """Search for items in memory matching the query."""
        inc_memory("search")
        return self.memory_store.search(query)

    def add_to_context(self, key: str, value: Any) -> None:
        """Add a value to the current context."""
        inc_memory("add_context")
        self.context_manager.add_to_context(key, value)

    def get_from_context(self, key: str) -> Any | None:
        """Get a value from the current context."""
        inc_memory("get_context")
        return self.context_manager.get_from_context(key)

    def get_full_context(self) -> dict[str, Any]:
        """Get the full current context."""
        inc_memory("get_full_context")
        return self.context_manager.get_full_context()
