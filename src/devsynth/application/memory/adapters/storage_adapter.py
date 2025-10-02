"""Storage adapter protocol for memory backends.

This protocol defines the minimal interface required for storage backends used
by :class:`~devsynth.application.memory.memory_manager.MemoryManager`.  Each
backend exposes its ``backend_type`` for configuration-based selection and
implements the :class:`~devsynth.domain.interfaces.memory.MemoryStore` contract.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar, Protocol

from ....domain.models.memory import MemoryItem, MemoryVector
from ..dto import (
    MemoryMetadata,
    MemoryQueryResults,
    MemoryRecord,
    MemorySearchQuery,
)

MemorySnapshot = dict[str, MemoryItem] | dict[str, MemoryVector]


class StorageAdapter(Protocol):
    """Protocol implemented by memory storage adapters.

    Adapters expose a class-level :attr:`backend_type` used by
    :class:`~devsynth.application.memory.memory_manager.MemoryManager` to select
    the appropriate backend at runtime.
    """

    backend_type: ClassVar[str]

    def store(self, item: MemoryItem, transaction_id: str | None = None) -> str:
        """Store an item in memory and return its ID."""

    def retrieve(self, item_id: str) -> MemoryItem | MemoryRecord | None:
        """Retrieve an item from memory by ID."""

    def search(
        self, query: MemorySearchQuery | MemoryMetadata
    ) -> MemoryQueryResults | list[MemoryRecord]:
        """Search for items in memory matching the query."""

    def delete(self, item_id: str) -> bool:
        """Delete an item from memory."""

    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a transaction and return the active ID."""
        ...

    def prepare_commit(self, transaction_id: str) -> bool:
        """Prepare to commit a transaction."""
        ...

    def commit_transaction(self, transaction_id: str | None = None) -> bool:
        """Commit a transaction."""
        ...

    def rollback_transaction(self, transaction_id: str | None = None) -> bool:
        """Rollback a transaction."""
        ...

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` if ``transaction_id`` is active."""
        ...

    def snapshot(self) -> MemorySnapshot:
        """Create a snapshot of the current state."""
        ...

    def restore(
        self, snapshot: Mapping[str, MemoryItem] | Mapping[str, MemoryVector]
    ) -> bool:
        """Restore the adapter from ``snapshot``."""
        ...
