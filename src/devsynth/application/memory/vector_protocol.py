"""Protocols describing the vector store adapter surface."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from ...domain.models.memory import MemoryVector
from .dto import MemoryRecord, VectorStoreStats

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from numpy.typing import NDArray
    import numpy as np

    NumpyEmbedding: TypeAlias = NDArray[np.floating[Any]]
else:  # pragma: no cover - runtime fallback
    NumpyEmbedding: TypeAlias = Sequence[float]

EmbeddingVector: TypeAlias = Sequence[float] | NumpyEmbedding


class VectorStoreProtocol(Protocol):
    """Structural protocol implemented by vector store adapters."""

    def store_vector(self, vector: MemoryVector) -> str:
        ...

    def retrieve_vector(self, vector_id: str) -> MemoryVector | MemoryRecord | None:
        ...

    def similarity_search(
        self, query_embedding: EmbeddingVector, top_k: int = 5
    ) -> list[MemoryRecord]:
        ...

    def delete_vector(self, vector_id: str) -> bool:
        ...

    def get_collection_stats(self) -> VectorStoreStats:
        ...
