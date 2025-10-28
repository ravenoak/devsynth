"""ChromaDB-backed vector memory adapter."""

from __future__ import annotations

import importlib
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from types import ModuleType
from typing import Any, cast
from collections.abc import Callable

# ``chromadb`` lacks stable typing information and triggers deep imports.
# Load it dynamically and coerce the factories into structural protocols so
# the rest of the module can rely on precise adapter types.
chromadb_module: ModuleType
Settings: type[object]
PersistentClientFactory: Callable[..., ChromaClientProtocol]
EphemeralClientFactory: Callable[..., ChromaClientProtocol]
try:  # pragma: no cover - optional dependency
    chromadb_module = importlib.import_module("chromadb")
    Settings = cast(
        type[object], getattr(importlib.import_module("chromadb.config"), "Settings")
    )
    PersistentClientFactory = cast(
        Callable[..., "ChromaClientProtocol"],
        getattr(chromadb_module, "PersistentClient"),
    )
    EphemeralClientFactory = cast(
        Callable[..., "ChromaClientProtocol"],
        getattr(chromadb_module, "EphemeralClient"),
    )
except Exception as e:  # pragma: no cover - if chromadb is missing the tests skip
    raise ImportError(
        "ChromaDBVectorAdapter requires the 'chromadb' package. Install it with "
        "'pip install chromadb' or use the dev extras."
    ) from e

from ....domain.models.memory import MemoryVector
from ....logging_setup import DevSynthLogger
from ..dto import MemoryMetadata, MemoryRecord, VectorStoreStats, build_memory_record
from ..metadata_serialization import from_serializable, to_serializable
from ..vector_protocol import VectorStoreProtocol
from ._chromadb_protocols import (
    ChromaClientProtocol,
    ChromaCollectionProtocol,
    ChromaGetResult,
    ChromaQueryResult,
)

logger = DevSynthLogger(__name__)


class ChromaDBVectorAdapter(VectorStoreProtocol):
    """
    ChromaDB Vector Adapter handles vector-based operations for similarity
    search using ChromaDB.

    It implements the VectorStore interface and provides methods for storing,
    retrieving, and searching vectors using ChromaDB as the backend.
    """

    def __init__(
        self, collection_name: str = "default", persist_directory: str | None = None
    ):
        """
        Initialize the ChromaDB Vector Adapter.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB data (if None,
                in-memory only)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.vectors: dict[str, MemoryVector] = {}

        self.client: ChromaClientProtocol
        if persist_directory:
            self.client = PersistentClientFactory(path=persist_directory)
        else:
            # Use an in-memory client when no directory is provided
            settings = Settings(anonymized_telemetry=False)
            self.client = EphemeralClientFactory(settings)

        self.collection: ChromaCollectionProtocol = (
            self.client.get_or_create_collection(collection_name)
        )
        logger.info(
            "ChromaDB Vector Adapter initialized with collection '%s'",
            collection_name,
        )

        # Storage for active transactions - maps transaction ID to snapshot
        self._active_transactions: dict[str, dict[str, MemoryVector]] = {}

    # ------------------------------------------------------------------
    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a transaction by taking a snapshot of current vectors."""
        transaction_id = transaction_id or str(uuid.uuid4())
        if transaction_id in self._active_transactions:
            raise ValueError(f"Transaction {transaction_id} already active")
        snapshot: dict[str, MemoryVector] = {
            v.id: deepcopy(v) for v in self.get_all_vectors()
        }
        self._active_transactions[transaction_id] = snapshot
        logger.debug("Began ChromaDB transaction %s", transaction_id)
        return transaction_id

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction by discarding its snapshot."""
        if transaction_id not in self._active_transactions:
            raise ValueError(f"Unknown transaction {transaction_id}")

        self._active_transactions.pop(transaction_id, None)
        logger.debug("Committed ChromaDB transaction %s", transaction_id)
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction by restoring the snapshot of vectors."""
        snapshot = self._active_transactions.pop(transaction_id, None)
        if snapshot is None:
            raise ValueError(f"Unknown transaction {transaction_id}")
        try:
            existing = self.collection.get(include=[]) or {}
            ids = existing.get("ids", []) if existing else []
            if ids:
                self.collection.delete(ids=ids)
            for vec in snapshot.values():
                self.collection.add(
                    ids=[vec.id],
                    embeddings=[vec.embedding],
                    metadatas=[
                        to_serializable(cast(MemoryMetadata | None, vec.metadata))
                    ],
                    documents=[vec.content],
                )
            self.vectors = snapshot
            logger.debug("Rolled back ChromaDB transaction %s", transaction_id)
            return True
        except Exception as e:  # pragma: no cover - defensive
            logger.error(
                "Error rolling back ChromaDB transaction %s: %s", transaction_id, e
            )
            return False

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` if the given transaction is currently active."""
        return transaction_id in self._active_transactions

    @contextmanager
    def transaction(self, transaction_id: str | None = None) -> Iterator[str]:
        """Context manager wrapper around transaction methods."""
        tid = self.begin_transaction(transaction_id)
        try:
            yield tid
            self.commit_transaction(tid)
        except Exception:
            self.rollback_transaction(tid)
            raise

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

        metadata_payload = cast(MemoryMetadata | None, vector.metadata)
        self.collection.add(
            ids=[vector.id],
            embeddings=[vector.embedding],
            metadatas=[to_serializable(metadata_payload)],
            documents=[vector.content],
        )

        self.vectors[vector.id] = vector
        logger.info("Stored memory vector with ID %s in ChromaDB", vector.id)
        return str(vector.id)

    def retrieve_vector(self, vector_id: str) -> MemoryRecord | None:
        """
        Retrieve a vector from the vector store.

        Args:
            vector_id: The ID of the vector to retrieve

        Returns:
            The retrieved vector, or None if not found
        """
        result = (
            self.collection.get(
                ids=[vector_id], include=["embeddings", "metadatas", "documents"]
            )
            or {}
        )
        if result and result.get("ids"):
            metadatas = result.get("metadatas") or []
            metadata_payload = metadatas[0] if metadatas else {}
            metadata: MemoryMetadata | None = None
            if isinstance(metadata_payload, Mapping):
                metadata = from_serializable(metadata_payload)
            documents = result.get("documents") or [None]
            embeddings = result.get("embeddings") or [[]]
            vector = MemoryVector(
                id=result["ids"][0],
                content=documents[0] if documents else None,
                embedding=embeddings[0] if embeddings else [],
                metadata=metadata,
            )
            self.vectors[vector_id] = vector
            return build_memory_record(vector, source="chromadb")
        return None

    def similarity_search(
        self, query_embedding: Sequence[float], top_k: int = 5
    ) -> list[MemoryRecord]:
        """
        Search for vectors similar to the query embedding.

        Args:
            query_embedding: The query embedding
            top_k: The number of results to return

        Returns:
            A list of similar memory vectors
        """
        results = (
            self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["embeddings", "metadatas", "documents"],
            )
            or {}
        )

        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        records: list[MemoryRecord] = []
        documents = results.get("documents") or [[None]]
        embeddings = results.get("embeddings") or [[[]]]
        metadatas = results.get("metadatas") or [[{}]]
        ids = results.get("ids") or [[]]
        for i, vid in enumerate(ids[0]):
            metadata_payload = metadatas[0][i] if metadatas and metadatas[0] else {}
            metadata: MemoryMetadata | None = None
            if isinstance(metadata_payload, Mapping):
                metadata = from_serializable(metadata_payload)
            vector = MemoryVector(
                id=vid,
                content=documents[0][i] if documents and documents[0] else None,
                embedding=embeddings[0][i] if embeddings and embeddings[0] else [],
                metadata=metadata,
            )
            self.vectors[vid] = vector
            records.append(build_memory_record(vector, source="chromadb"))

        return records

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

    def get_collection_stats(self) -> VectorStoreStats:
        """
        Get statistics about the vector store collection.

        Returns:
            A dictionary of statistics
        """
        # Note: In a real implementation, we would get stats from ChromaDB
        # count = self.collection.count()

        result = self.collection.get(include=["embeddings"]) or {}
        ids = result.get("ids", [])
        count = len(ids)
        dimension = 0
        embeddings = result.get("embeddings")
        if count > 0 and embeddings:
            first = embeddings[0]
            dimension = len(first) if not hasattr(first, "shape") else first.shape[0]

        return {
            "vector_count": count,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "embedding_dimensions": dimension,
        }

    def get_all_vectors(self) -> list[MemoryVector]:
        """Return all vectors stored in the adapter."""
        if self.vectors:
            return list(self.vectors.values())

        result = (
            self.collection.get(include=["embeddings", "metadatas", "documents"]) or {}
        )
        vectors: list[MemoryVector] = []
        ids = result.get("ids") or []
        documents = result.get("documents") or [None]
        embeddings = result.get("embeddings") or [[]]
        metadatas = result.get("metadatas") or [{}]
        for i, vid in enumerate(ids):
            metadata_payload = metadatas[i] if i < len(metadatas) else {}
            metadata: MemoryMetadata | None = None
            if isinstance(metadata_payload, Mapping):
                metadata = from_serializable(metadata_payload)
            vectors.append(
                MemoryVector(
                    id=vid,
                    content=documents[i] if i < len(documents) else None,
                    embedding=embeddings[i] if i < len(embeddings) else [],
                    metadata=metadata,
                )
            )
        for vec in vectors:
            self.vectors[vec.id] = vec
        return vectors
