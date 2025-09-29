from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from ...domain.models.memory import MemoryItem, MemoryVector

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from ...application.memory.dto import (
        GroupedMemoryResults,
        MemoryMetadata,
        MemoryQueryResults,
        MemoryRecord,
    )
else:
    MemoryRecord = MemoryItem  # type: ignore[assignment]
    from typing import MutableMapping

    MemoryMetadata = MutableMapping[str, Any]

MemorySearchResponse: TypeAlias = (
    list[MemoryItem]
    | list["MemoryRecord"]
    | "MemoryQueryResults"
    | "GroupedMemoryResults"
)
"""Permissible result shapes returned from ``MemoryStore.search`` implementations."""


class MemoryStore(Protocol):
    """Protocol for memory storage."""

    @abstractmethod
    def store(self, item: MemoryItem) -> str:
        """Store an item in memory and return its ID."""
        ...

    @abstractmethod
    def retrieve(self, item_id: str) -> MemoryItem | "MemoryRecord" | None:
        """Retrieve an item from memory by ID."""
        ...

    @abstractmethod
    def search(self, query: dict[str, Any] | "MemoryMetadata") -> MemorySearchResponse:
        """Search for items in memory matching the query.

        Adapters may return bare ``MemoryItem`` instances for legacy callers,
        enriched ``MemoryRecord`` objects, or aggregated payloads using the
        DTOs from :mod:`devsynth.application.memory.dto`.
        """
        ...

    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """Delete an item from memory."""
        ...

    @abstractmethod
    def begin_transaction(self) -> str:
        """Begin a new transaction and return a transaction ID.

        Transactions provide atomicity for a series of operations.
        All operations within a transaction either succeed or fail together.
        """
        ...

    @abstractmethod
    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction, making all its operations permanent.

        Args:
            transaction_id: The ID of the transaction to commit

        Returns:
            True if the transaction was committed successfully, False otherwise
        """
        ...

    @abstractmethod
    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction, undoing all its operations.

        Args:
            transaction_id: The ID of the transaction to rollback

        Returns:
            True if the transaction was rolled back successfully, False otherwise
        """
        ...

    @abstractmethod
    def is_transaction_active(self, transaction_id: str) -> bool:
        """Check if a transaction is active.

        Args:
            transaction_id: The ID of the transaction to check

        Returns:
            True if the transaction is active, False otherwise
        """
        ...


class VectorStore(Protocol):
    """Protocol for vector storage."""

    @abstractmethod
    def store_vector(self, vector: MemoryVector) -> str:
        """Store a vector in the vector store and return its ID."""
        ...

    @abstractmethod
    def retrieve_vector(self, vector_id: str) -> MemoryVector | "MemoryRecord" | None:
        """Retrieve a vector from the vector store by ID."""
        ...

    @abstractmethod
    def similarity_search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[MemoryVector] | list["MemoryRecord"]:
        """Search for vectors similar to the query embedding."""
        ...

    @abstractmethod
    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the vector store."""
        ...

    @abstractmethod
    def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the vector store collection."""
        ...


class ContextManager(Protocol):
    """Protocol for managing context."""

    @abstractmethod
    def add_to_context(self, key: str, value: Any) -> None:
        """Add a value to the current context."""
        ...

    @abstractmethod
    def get_from_context(self, key: str) -> Any | None:
        """Get a value from the current context."""
        ...

    @abstractmethod
    def get_full_context(self) -> dict[str, Any]:
        """Get the full current context."""
        ...

    @abstractmethod
    def clear_context(self) -> None:
        """Clear the current context."""
        ...


class VectorStoreProviderFactory(Protocol):
    """Protocol for creating :class:`VectorStore` providers."""

    @abstractmethod
    def create_provider(
        self, provider_type: str, config: dict[str, Any] | None = None
    ) -> VectorStore:
        """Create a VectorStore provider of the specified type."""
        ...

    @abstractmethod
    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        """Register a new provider type."""
        ...
