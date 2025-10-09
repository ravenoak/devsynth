"""Port for vector storage operations."""

from __future__ import annotations

from typing import Any

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ..application.memory.dto import VectorStoreStats
from ..domain.interfaces.memory import VectorStore
from ..domain.models.memory import MemoryVector

logger = DevSynthLogger(__name__)


class VectorStorePort:
    """Port for vector storage operations."""

    def __init__(self, vector_store: VectorStore[MemoryVector]):
        self.vector_store = vector_store

    def store_vector(
        self,
        content: Any,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a vector in the vector store and return its ID."""
        vector = MemoryVector(
            id="", content=content, embedding=embedding, metadata=metadata
        )
        return self.vector_store.store_vector(vector)

    def retrieve_vector(self, vector_id: str) -> MemoryVector | None:
        """Retrieve a vector from the vector store by ID."""
        return self.vector_store.retrieve_vector(vector_id)

    def similarity_search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[MemoryVector]:
        """Search for vectors similar to the query embedding."""
        return self.vector_store.similarity_search(query_embedding, top_k)

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the vector store."""
        return self.vector_store.delete_vector(vector_id)

    def get_collection_stats(self) -> VectorStoreStats:
        """Get statistics about the vector store collection."""
        return self.vector_store.get_collection_stats()
