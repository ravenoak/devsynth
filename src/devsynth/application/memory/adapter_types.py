"""Typed adapter aliases shared across memory components."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol, TypeAlias, runtime_checkable

from ...domain.interfaces.memory import MemoryStore
from ...domain.models.memory import MemoryItem, MemoryType
from .dto import (
    MemoryMetadata,
    MemoryMetadataValue,
    MemoryQueryResults,
    MemoryRecord,
    MemoryRecordInput,
    MemorySearchQuery,
)
from .vector_protocol import VectorStoreProtocol

StructuredQueryRow: TypeAlias = Mapping[
    str,
    MemoryMetadataValue | Sequence[MemoryMetadataValue] | MemoryItem | MemoryMetadata,
]


@runtime_checkable
class SupportsStructuredQuery(Protocol):
    """Protocol for adapters that expose structured query helpers."""

    def query_structured_data(
        self, query: MemorySearchQuery
    ) -> Sequence[StructuredQueryRow] | MemoryQueryResults:
        """Return structured query results for ``query``."""


@runtime_checkable
class SupportsEdrrRetrieval(Protocol):
    """Protocol for adapters providing EDRR-specific retrieval helpers."""

    def retrieve_with_edrr_phase(
        self,
        item_type: MemoryType,
        edrr_phase: str,
        metadata: MemoryMetadata,
    ) -> MemoryItem | MemoryRecord | None:
        """Return a memory artefact tagged with ``edrr_phase``."""


@runtime_checkable
class SupportsGraphQueries(Protocol):
    """Protocol for adapters exposing graph relationship traversal."""

    def query_related_items(self, item_id: str) -> Iterable[MemoryItem]:
        """Return memory items related to ``item_id``."""


@runtime_checkable
class SupportsRetrieve(Protocol):
    """Protocol for adapters exposing ``retrieve`` operations."""

    def retrieve(self, item_id: str) -> MemoryItem | MemoryRecord | None:
        """Return a memory artefact identified by ``item_id``."""


@runtime_checkable
class SupportsSearch(Protocol):
    """Protocol for adapters exposing ``search`` helpers."""

    def search(
        self, query: MemorySearchQuery | MemoryMetadata
    ) -> Sequence[MemoryRecordInput] | MemoryRecordInput | MemoryQueryResults:
        """Return search results for ``query``."""


MemoryAdapter: TypeAlias = MemoryStore | VectorStoreProtocol
"""Union of supported adapter surfaces managed by :class:`MemoryManager`."""


AdapterRegistry: TypeAlias = dict[str, MemoryAdapter]
"""Concrete mapping used for adapter registries across the memory stack."""


__all__ = [
    "AdapterRegistry",
    "MemoryAdapter",
    "StructuredQueryRow",
    "SupportsStructuredQuery",
    "SupportsEdrrRetrieval",
    "SupportsGraphQueries",
    "SupportsRetrieve",
    "SupportsSearch",
]
