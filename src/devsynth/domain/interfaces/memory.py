"""Typed protocols for domain memory backends and vector stores.

The previous ``MemoryStore``/``VectorStore`` interfaces were intentionally lax
to ease early adapter development.  As more infrastructure layers began relying
on structured responses, the ``Any``-heavy contracts started to hinder static
analysis and led to defensive runtime checks spread across the code base.  This
module now exposes covariant, typed protocols that describe the guarantees a
backend provides.  Implementations can opt into helper protocols, such as
``SupportsTransactions`` and ``SupportsStats``, when they support additional
behaviour without forcing every store to implement those methods.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, TypeVar, Union

if TYPE_CHECKING:  # pragma: no cover - imports for static analysis only
    from ...application.memory.dto import GroupedMemoryResults as _GroupedMemoryResults
    from ...application.memory.dto import MemoryMetadata as _MemoryMetadata
    from ...application.memory.dto import MemoryMetadataValue as _MemoryMetadataValue
    from ...application.memory.dto import MemoryQueryResults as _MemoryQueryResults
    from ...application.memory.dto import MemoryRecord as _MemoryRecord
    from ...application.memory.dto import VectorStoreStats as _VectorStoreStats
else:  # pragma: no cover - runtime fallbacks avoid optional dependency imports
    _GroupedMemoryResults = Mapping[str, Any]
    _MemoryMetadata = Mapping[str, Any]
    _MemoryMetadataValue = Any
    _MemoryQueryResults = Mapping[str, Any]
    _MemoryRecord = Any
    _VectorStoreStats = Mapping[str, Any]
from ...domain.models.memory import MemoryItem, MemoryVector

MemoryMetadata: TypeAlias = _MemoryMetadata
"""Normalized metadata mapping carried alongside memory artefacts."""

MemoryMetadataValue: TypeAlias = _MemoryMetadataValue
"""Supported value types for metadata attached to memory artefacts."""

MemoryQueryResults: TypeAlias = _MemoryQueryResults
"""Results returned by querying a single memory store."""

GroupedMemoryResults: TypeAlias = _GroupedMemoryResults
"""Aggregated search responses combining multiple query results."""

MemoryRecord: TypeAlias = _MemoryRecord
"""Normalized memory record returned from store-agnostic search APIs."""

VectorStoreStats: TypeAlias = _VectorStoreStats
"""Normalized statistics returned by vector-backed adapters."""

MemoryMetadataMapping: TypeAlias = Mapping[str, MemoryMetadataValue]
"""Structural alias capturing the metadata mapping contract for backends."""

TRecord_co = TypeVar("TRecord_co", covariant=True)
TMetadata_contra = TypeVar(
    "TMetadata_contra", bound=MemoryMetadataMapping, contravariant=True
)
TVectorRecord = TypeVar("TVectorRecord")
TStats_co = TypeVar("TStats_co", covariant=True)

MemorySearchResponse: TypeAlias = Union[
    list[MemoryItem],
    list[MemoryRecord],
    MemoryQueryResults,
    GroupedMemoryResults,
]
"""Permissible result shapes returned from ``MemoryBackend.search`` implementations."""


class SupportsTransactions(Protocol):
    """Structural protocol for stores offering transactional guarantees."""

    def begin_transaction(self) -> str:
        """Begin a new transaction and return its identifier."""

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction, making all its operations permanent."""

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction, undoing all operations inside the scope."""

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` if the transaction is still active."""


class TransactionalMemory(SupportsTransactions, Protocol):
    """ABC-style protocol for transactional memory backends."""

    @abstractmethod
    def begin_transaction(self) -> str: ...

    @abstractmethod
    def commit_transaction(self, transaction_id: str) -> bool: ...

    @abstractmethod
    def rollback_transaction(self, transaction_id: str) -> bool: ...

    @abstractmethod
    def is_transaction_active(self, transaction_id: str) -> bool: ...


class SupportsStats(Protocol[TStats_co]):
    """Helper protocol for stores that can expose collection statistics."""

    def get_collection_stats(self) -> TStats_co:
        """Return an implementation-defined statistics payload."""


class MemoryBackend(Protocol[TRecord_co, TMetadata_contra]):
    """Protocol describing the capabilities required from memory backends."""

    @abstractmethod
    def store(self, item: MemoryItem) -> str:
        """Persist a :class:`~devsynth.domain.models.memory.MemoryItem`."""

    @abstractmethod
    def retrieve(self, item_id: str) -> TRecord_co | None:
        """Retrieve an item from memory by identifier."""

    @abstractmethod
    def search(
        self, query: Mapping[str, object] | TMetadata_contra
    ) -> MemorySearchResponse:
        """Search for items in memory matching the query payload."""

    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """Delete an item from memory by identifier."""


class MemoryStore(MemoryBackend[MemoryItem | MemoryRecord, MemoryMetadata], Protocol):
    """Backward compatible protocol for stores emitting items or records."""


class VectorStore(SupportsStats[VectorStoreStats], Protocol[TVectorRecord]):
    """Protocol for vector storage backends returning ``TVector_co`` entries."""

    @abstractmethod
    def store_vector(self, vector: MemoryVector) -> str:
        """Store a vector in the vector store and return its identifier."""

    @abstractmethod
    def retrieve_vector(self, vector_id: str) -> TVectorRecord | None:
        """Retrieve a vector from the vector store by identifier."""

    @abstractmethod
    def similarity_search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[TVectorRecord]:
        """Return the ``top_k`` closest matches for ``query_embedding``."""

    @abstractmethod
    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the vector store."""


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


class VectorStoreProviderFactory(Protocol[TVectorRecord]):
    """Protocol for creating typed :class:`VectorStore` providers."""

    @abstractmethod
    def create_provider(
        self, provider_type: str, config: dict[str, Any] | None = None
    ) -> VectorStore[TVectorRecord]:
        """Create a VectorStore provider of the specified type."""
        ...

    @abstractmethod
    def register_provider_type(
        self, provider_type: str, provider_class: type[VectorStore[TVectorRecord]]
    ) -> None:
        """Register a new provider type."""
        ...
