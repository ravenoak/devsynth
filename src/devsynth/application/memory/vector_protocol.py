"""Protocols describing the vector store adapter surface."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from ...domain.models.memory import MemoryVector
from .dto import MemoryRecord


class VectorStoreProtocol(Protocol):
    """Structural protocol implemented by vector store adapters."""

    def store_vector(self, vector: MemoryVector) -> str:
        ...

    def retrieve_vector(self, vector_id: str) -> MemoryVector | MemoryRecord | None:
        ...

    def similarity_search(
        self, query_embedding: Sequence[float], top_k: int = 5
    ) -> list[MemoryRecord] | list[MemoryVector]:
        ...

    def delete_vector(self, vector_id: str) -> bool:
        ...

    def get_collection_stats(self) -> dict[str, Any]:
        ...
