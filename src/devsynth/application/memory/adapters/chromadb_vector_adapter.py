"""
ChromaDB Vector Adapter Module

This module provides a memory adapter that handles vector-based operations
for similarity search using ChromaDB as the backend.
"""

"""
Adapter for using ChromaDB as a simple vector store.

The previous implementation only stored vectors in a local dictionary.  This
update provides real interactions with ChromaDB using its client API so that
vectors are persisted and retrieved from a ChromaDB collection.
"""

from typing import Any, Dict, List, Optional

import numpy as np

try:  # pragma: no cover - optional dependency
    import chromadb
    from chromadb.config import Settings
except Exception as e:  # pragma: no cover - if chromadb is missing the tests skip
    raise ImportError(
        "ChromaDBVectorAdapter requires the 'chromadb' package. Install it with 'pip install chromadb' or use the dev extras."
    ) from e

from ....domain.models.memory import MemoryVector
from ....domain.interfaces.memory import VectorStore
from ....logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ChromaDBVectorAdapter(VectorStore):
    """
    ChromaDB Vector Adapter handles vector-based operations for similarity search using ChromaDB.

    It implements the VectorStore interface and provides methods for storing,
    retrieving, and searching vectors using ChromaDB as the backend.
    """

    def __init__(
        self, collection_name: str = "default", persist_directory: Optional[str] = None
    ):
        """
        Initialize the ChromaDB Vector Adapter.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB data (if None, in-memory only)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.vectors: Dict[str, MemoryVector] = {}

        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            # Use an in-memory client when no directory is provided
            settings = Settings(anonymized_telemetry=False)
            self.client = chromadb.EphemeralClient(settings)

        self.collection = self.client.get_or_create_collection(collection_name)
        logger.info(
            "ChromaDB Vector Adapter initialized with collection '%s'", collection_name
        )

    def store_vector(self, vector: MemoryVector) -> str:
        """
        Store a vector in the vector store.

        Args:
            vector: The memory vector to store

        Returns:
            The ID of the stored vector
        """
        if not vector.id:
            vector.id = f"vector_{len(self.vectors) + 1}"

        self.collection.add(
            ids=[vector.id],
            embeddings=[vector.embedding],
            metadatas=[vector.metadata or {}],
            documents=[vector.content],
        )

        self.vectors[vector.id] = vector
        logger.info("Stored memory vector with ID %s in ChromaDB", vector.id)
        return vector.id

    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:
        """
        Retrieve a vector from the vector store.

        Args:
            vector_id: The ID of the vector to retrieve

        Returns:
            The retrieved vector, or None if not found
        """
        result = self.collection.get(
            ids=[vector_id], include=["embeddings", "metadatas", "documents"]
        )
        if result and result.get("ids"):
            vector = MemoryVector(
                id=result["ids"][0],
                content=result.get("documents", [None])[0],
                embedding=result.get("embeddings", [[None]])[0],
                metadata=result.get("metadatas", [{}])[0],
            )
            self.vectors[vector_id] = vector
            return vector
        return None

    def similarity_search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[MemoryVector]:
        """
        Search for vectors similar to the query embedding.

        Args:
            query_embedding: The query embedding
            top_k: The number of results to return

        Returns:
            A list of similar memory vectors
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["embeddings", "metadatas", "documents"],
        )

        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        vectors = []
        for i, vid in enumerate(results["ids"][0]):
            vector = MemoryVector(
                id=vid,
                content=results.get("documents", [[None]])[0][i],
                embedding=results.get("embeddings", [[None]])[0][i],
                metadata=results.get("metadatas", [[{}]])[0][i],
            )
            self.vectors[vid] = vector
            vectors.append(vector)

        return vectors

    def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector from the vector store.

        Args:
            vector_id: The ID of the vector to delete

        Returns:
            True if the vector was deleted, False otherwise
        """
        result = self.collection.get(ids=[vector_id])
        if not result or not result.get("ids"):
            return False

        self.collection.delete(ids=[vector_id])
        self.vectors.pop(vector_id, None)
        logger.info("Deleted memory vector with ID %s from ChromaDB", vector_id)
        return True

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            A dictionary of statistics
        """
        # Note: In a real implementation, we would get stats from ChromaDB
        # count = self.collection.count()

        result = self.collection.get(include=["embeddings"])
        count = len(result.get("ids", [])) if result else 0
        dimension = 0
        if count > 0 and result.get("embeddings"):
            first = result["embeddings"][0]
            dimension = len(first) if not hasattr(first, "shape") else first.shape[0]

        return {
            "vector_count": count,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "embedding_dimensions": dimension,
        }

    def get_all_vectors(self) -> List[MemoryVector]:
        """Return all vectors stored in the adapter."""
        if self.vectors:
            return list(self.vectors.values())

        result = self.collection.get(include=["embeddings", "metadatas", "documents"])
        vectors: List[MemoryVector] = []
        for i, vid in enumerate(result.get("ids", [])):
            vectors.append(
                MemoryVector(
                    id=vid,
                    content=result.get("documents", [[None]])[0][i],
                    embedding=result.get("embeddings", [[None]])[0][i],
                    metadata=result.get("metadatas", [[{}]])[0][i],
                )
            )
        for vec in vectors:
            self.vectors[vec.id] = vec
        return vectors
