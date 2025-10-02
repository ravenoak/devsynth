"""Typed adapter aliases shared across memory components."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol, TypeAlias, runtime_checkable

from ...domain.interfaces.memory import MemoryStore
from ...domain.models.memory import MemoryItem, MemoryType
from .dto import (
    MemoryMetadataValue,
    MemoryQueryResults,
    MemoryRecord,
    MemorySearchQuery,
)
from .vector_protocol import VectorStoreProtocol


@runtime_checkable
class SupportsStructuredQuery(Protocol):
    """Protocol for adapters that expose structured query helpers."""

    def query_structured_data(
        self, query: MemorySearchQuery
    ) -> Sequence[Mapping[str, object]] | MemoryQueryResults:
        """Return structured query results for ``query``."""


@runtime_checkable
class SupportsEdrrRetrieval(Protocol):
    """Protocol for adapters providing EDRR-specific retrieval helpers."""

    def retrieve_with_edrr_phase(
        self,
        item_type: MemoryType,
        edrr_phase: str,
        metadata: Mapping[str, MemoryMetadataValue],
    ) -> MemoryItem | MemoryRecord | None:
        """Return a memory artefact tagged with ``edrr_phase``."""


@runtime_checkable
class SupportsGraphQueries(Protocol):
    """Protocol for adapters exposing graph relationship traversal."""

    def query_related_items(self, item_id: str) -> Iterable[MemoryItem]:
        """Return memory items related to ``item_id``."""


MemoryAdapter: TypeAlias = MemoryStore | VectorStoreProtocol
"""Union of supported adapter surfaces managed by :class:`MemoryManager`."""


AdapterRegistry: TypeAlias = dict[str, MemoryAdapter]
"""Concrete mapping used for adapter registries across the memory stack."""


__all__ = [
    "AdapterRegistry",
    "MemoryAdapter",
    "SupportsStructuredQuery",
    "SupportsEdrrRetrieval",
    "SupportsGraphQueries",
]
