"""FAISS-backed vector store implementation."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np
import tiktoken

if TYPE_CHECKING:  # pragma: no cover - typing only import
    import faiss as faiss_module
    from faiss import Index, IndexFlatL2
else:  # pragma: no cover - runtime fallback type alias
    faiss_module = ModuleType

faiss: faiss_module | None
try:  # pragma: no cover - optional dependency import
    import faiss as _faiss
except Exception:  # pragma: no cover - graceful fallback when unavailable
    faiss = None
else:
    faiss = cast("faiss_module", _faiss)

from devsynth.exceptions import MemoryError, MemoryItemNotFoundError, MemoryStoreError
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.memory import SupportsTransactions, VectorStore
from ...domain.models.memory import MemoryItem, MemoryVector
from .dto import MemoryMetadata, MemoryRecord, VectorStoreStats, build_memory_record
from .metadata_serialization import from_serializable, to_serializable

# Create a logger for this module
logger = DevSynthLogger(__name__)


class _StoredVectorEntry(TypedDict, total=False):
    """Serialized representation persisted for each FAISS vector."""

    content: str | None
    embedding: list[float]
    metadata: dict[str, object]
    created_at: str
    index: int
    is_deleted: bool


@dataclass(slots=True)
class _Snapshot:
    """Snapshot of index state captured for transactional rollbacks."""

    index: "Index"
    metadata: dict[str, _StoredVectorEntry]


class FAISSStore(VectorStore[MemoryRecord], SupportsTransactions):
    """
    FAISS implementation of the VectorStore interface.

    This class uses FAISS for efficient vector similarity search.
    """

    def __init__(self, base_path: str, dimension: int = 5):
        """
        Initialize a FAISSStore.

        Args:
            base_path: Base path for storing the FAISS index and metadata
            dimension: Dimension of the vectors to store (default: 5)
        """
        module = faiss
        if module is None:
            raise ImportError(
                "FAISSStore requires the 'faiss' package. Install it with 'pip install faiss-cpu' "
                "or enable the retrieval extra."
            )

        self._module = module
        self.base_path = base_path
        self.index_file = os.path.join(self.base_path, "faiss_index.bin")
        self.metadata_file = os.path.join(self.base_path, "metadata.json")
        self.token_count = 0
        self.dimension = dimension
        self.metadata: dict[str, _StoredVectorEntry] = {}
        self.index = cast("Index", self._module.IndexFlatL2(max(1, self.dimension)))

        # Ensure the directory exists
        os.makedirs(self.base_path, exist_ok=True)

        # Initialize the tokenizer for token counting
        self.tokenizer: object | None = None
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding
        except Exception as e:
            logger.warning(
                f"Failed to initialize tokenizer: {e}. Token counting will be approximate."
            )

        # Initialize FAISS index and metadata
        self._initialize_store()

        # Track transaction snapshots.  Each active transaction stores a
        # cloned FAISS index and metadata dictionary so that rollback can
        # restore the previous state if an error occurs.
        self._snapshots: dict[str, _Snapshot] = {}

    def _initialize_store(self) -> None:
        """Initialize the FAISS index and metadata store."""
        try:
            # Initialize metadata dictionary
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, "r", encoding="utf-8") as fh:
                    raw_metadata = json.load(fh)
                self.metadata: dict[str, _StoredVectorEntry] = {
                    key: cast(_StoredVectorEntry, value)
                    for key, value in raw_metadata.items()
                    if isinstance(value, Mapping)
                }
                # Get dimension from existing metadata
                if self.metadata:
                    first_id = next(iter(self.metadata))
                    embedding = self.metadata[first_id].get("embedding", [])
                    if embedding:
                        self.dimension = len(embedding)
            else:
                self.metadata = {}

            # Initialize or load FAISS index
            if os.path.exists(self.index_file):
                self.index = cast("Index", self._module.read_index(self.index_file))
                logger.info(f"Loaded existing FAISS index from {self.index_file}")
            else:
                # Create a new index - using L2 distance (Euclidean)
                self.index = cast("Index", self._module.IndexFlatL2(self.dimension))
                logger.info(f"Created new FAISS index with dimension {self.dimension}")

            logger.info("FAISS store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS store: {e}")
            raise MemoryStoreError(f"Failed to initialize FAISS store: {e}")

    def _save_index(self) -> None:
        """Save the FAISS index to disk."""
        try:
            self._module.write_index(self.index, self.index_file)
            logger.info(f"Saved FAISS index to {self.index_file}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            raise MemoryStoreError(f"Failed to save FAISS index: {e}")

    def _save_metadata(self) -> None:
        """Save the metadata to disk."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as fh:
                json.dump(self.metadata, fh)
            logger.info(f"Saved metadata to {self.metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise MemoryStoreError(f"Failed to save metadata: {e}")

    def _count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text
        """
        if self.tokenizer:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        else:
            # Approximate token count (roughly 4 characters per token)
            return len(text) // 4

    def _serialize_metadata(self, metadata: MemoryMetadata | None) -> dict[str, object]:
        """Normalize ``MemoryMetadata`` for JSON persistence."""

        serialized = to_serializable(metadata)
        return dict(serialized)

    def _deserialize_metadata(
        self, metadata: Mapping[str, object] | None
    ) -> MemoryMetadata:
        """Restore ``MemoryMetadata`` from serialized payloads."""

        if metadata is None or not isinstance(metadata, Mapping):
            return {}
        return from_serializable(metadata)

    # ------------------------------------------------------------------
    # Transaction management

    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a new transaction and return its identifier."""

        tx_id = transaction_id or str(uuid.uuid4())
        if tx_id in self._snapshots:
            raise MemoryStoreError(f"Transaction {tx_id} already active")
        # Clone index and metadata for rollback
        try:
            serialized = self._module.serialize_index(self.index)
            index_clone = cast("Index", self._module.deserialize_index(serialized))
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to snapshot FAISS index: {exc}")
            raise MemoryStoreError("Failed to snapshot FAISS index")
        self._snapshots[tx_id] = _Snapshot(
            index=index_clone,
            metadata=deepcopy(self.metadata),
        )
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a previously started transaction."""

        if transaction_id not in self._snapshots:
            raise MemoryStoreError(
                f"Commit requested for unknown transaction {transaction_id}"
            )
        self._snapshots.pop(transaction_id, None)
        self._save_index()
        self._save_metadata()
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback to the snapshot captured at transaction start."""

        snap = self._snapshots.pop(transaction_id, None)
        if snap is None:
            raise MemoryStoreError(
                f"Rollback requested for unknown transaction {transaction_id}"
            )
        self.index = snap.index
        self.metadata = snap.metadata
        self._save_index()
        self._save_metadata()
        return True

    @contextmanager
    def transaction(self, transaction_id: str | None = None) -> Iterator[str]:
        """Context manager providing transactional semantics."""

        tx_id: str = self.begin_transaction(transaction_id)
        try:
            yield tx_id
        except Exception:
            self.rollback_transaction(tx_id)
            raise
        else:
            self.commit_transaction(tx_id)

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` when ``transaction_id`` corresponds to a snapshot."""

        return transaction_id in self._snapshots

    def _build_record(
        self,
        vector_id: str,
        entry: _StoredVectorEntry,
        *,
        similarity: float | None = None,
    ) -> MemoryRecord:
        """Construct a :class:`MemoryRecord` from serialized vector metadata."""

        metadata_payload = self._deserialize_metadata(entry.get("metadata"))
        created_at = (
            datetime.fromisoformat(entry["created_at"])
            if entry.get("created_at")
            else None
        )
        vector = MemoryVector(
            id=vector_id,
            content=entry.get("content"),
            embedding=list(entry.get("embedding", [])),
            metadata=metadata_payload,
            created_at=created_at,
        )
        return build_memory_record(
            vector,
            source=self.__class__.__name__,
            similarity=similarity,
            metadata=metadata_payload,
        )

    def store_vector(self, vector: MemoryVector) -> str:
        """
        Store a vector in the vector store and return its ID.

        Args:
            vector: The MemoryVector to store

        Returns:
            The ID of the stored vector

        Raises:
            MemoryStoreError: If the vector cannot be stored
        """
        try:
            # Generate an ID if not provided
            if not vector.id:
                vector.id = str(uuid.uuid4())

            # Convert embedding to numpy array
            embedding = np.array(vector.embedding, dtype=np.float32)

            # Reshape for FAISS (expects 2D array)
            embedding = embedding.reshape(1, -1)

            # Update dimension if this is the first vector
            if len(self.metadata) == 0:
                self.dimension = embedding.shape[1]
                # Reinitialize the index with the correct dimension
                self.index = cast("Index", self._module.IndexFlatL2(self.dimension))

            # Check if the vector already exists
            if vector.id in self.metadata:
                # Get the index of the existing vector
                idx = self.metadata[vector.id].get("index")
                if idx is not None:
                    # Remove the existing vector (not directly supported by FAISS, so we'll handle in metadata)
                    self.metadata[vector.id]["is_deleted"] = True

            # Add the vector to the index
            self.index.add(embedding)

            # Get the index of the added vector
            idx = self.index.ntotal - 1

            # Store metadata
            self.metadata[vector.id] = {
                "content": vector.content,
                "embedding": list(vector.embedding),
                "metadata": self._serialize_metadata(vector.metadata or {}),
                "created_at": (
                    vector.created_at.isoformat()
                    if vector.created_at
                    else datetime.now().isoformat()
                ),
                "index": idx,
                "is_deleted": False,
            }
            # Persist immediately only when not inside a transaction
            if not self._snapshots:
                self._save_index()
                self._save_metadata()

            logger.info(f"Stored vector with ID {vector.id} in FAISS")
            return vector.id

        except Exception as e:
            logger.error(f"Failed to store vector in FAISS: {e}")
            raise MemoryStoreError(f"Failed to store vector: {e}")

    def retrieve_vector(self, vector_id: str) -> MemoryRecord | None:
        """
        Retrieve a vector from the vector store by ID.

        Args:
            vector_id: The ID of the vector to retrieve

        Returns:
            The retrieved :class:`MemoryRecord`, or ``None`` if not found

        Raises:
            MemoryStoreError: If there is an error retrieving the vector
        """
        try:
            # Check if the vector exists in metadata
            if vector_id not in self.metadata:
                logger.warning(f"Vector with ID {vector_id} not found in FAISS")
                return None

            # Get the metadata for the vector
            vector_metadata = self.metadata[vector_id]

            # Check if the vector is marked as deleted
            if vector_metadata.get("is_deleted", False):
                logger.warning(f"Vector with ID {vector_id} is marked as deleted")
                return None

            record = self._build_record(vector_id, vector_metadata)

            # Update token count
            token_count = self._count_tokens(str(record.item))
            self.token_count += token_count

            logger.info(f"Retrieved vector with ID {vector_id} from FAISS")
            return record

        except Exception as e:
            logger.error(f"Error retrieving vector from FAISS: {e}")
            raise MemoryStoreError(f"Error retrieving vector: {e}")

    def similarity_search(
        self, query_embedding: Sequence[float], top_k: int = 5
    ) -> list[MemoryRecord]:
        """
        Search for vectors similar to the query embedding.

        Args:
            query_embedding: The embedding to search for
            top_k: The number of results to return

        Returns:
            A list of :class:`MemoryRecord` entries similar to the query embedding

        Raises:
            MemoryStoreError: If there is an error performing the search
        """
        try:
            # Convert query_embedding to numpy array
            query = np.array(list(query_embedding), dtype=np.float32)

            # Reshape for FAISS (expects 2D array)
            query = query.reshape(1, -1)

            # Check if there are any vectors in the index
            if self.index.ntotal == 0:
                logger.warning("No vectors in the index for similarity search")
                return []

            # Check if dimensions match
            if query.shape[1] != self.dimension:
                logger.error(
                    f"Query dimension {query.shape[1]} does not match index dimension {self.dimension}"
                )
                raise MemoryStoreError(
                    f"Query dimension {query.shape[1]} does not match index dimension {self.dimension}"
                )

            # Adjust top_k if it's larger than the number of vectors
            effective_top_k = min(top_k, self.index.ntotal)

            # Ensure the index is properly initialized
            index_flat_l2 = getattr(self._module, "IndexFlatL2", None)
            if index_flat_l2 is not None and not isinstance(self.index, index_flat_l2):
                logger.warning("FAISS index is not properly initialized, recreating it")
                self.index = cast("Index", self._module.IndexFlatL2(self.dimension))
                # If we had to recreate the index, we need to return empty results
                # since the index no longer contains the vectors
                return []

            # Verify the index is not empty and is properly trained
            if self.index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return []

            # Ensure the query is properly formatted
            if not np.isfinite(query).all():
                logger.error("Query contains non-finite values (NaN or Inf)")
                return []

            try:
                # Perform the search with additional error handling
                distances, indices = self.index.search(query, effective_top_k)
            except RuntimeError as e:
                logger.error(f"FAISS search runtime error: {e}")
                return []
            except ValueError as e:
                logger.error(f"FAISS search value error: {e}")
                return []
            except MemoryError as e:
                logger.error(f"FAISS search memory error: {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error during FAISS search: {e}")
                return []

            # Validate search results
            if indices is None or len(indices) == 0:
                logger.warning("FAISS search returned no indices")
                return []

            # Map indices to vector IDs
            results: list[MemoryRecord] = []
            for position, idx in enumerate(indices[0]):
                # Skip invalid indices
                if idx < 0 or idx >= self.index.ntotal:
                    logger.warning(f"Skipping invalid index {idx}")
                    continue

                # Find the vector ID for this index
                vector_id: str | None = None
                entry: _StoredVectorEntry | None = None
                for vid, meta in self.metadata.items():
                    if meta.get("index") == idx and not meta.get("is_deleted", False):
                        vector_id = vid
                        entry = meta
                        break

                if vector_id and entry is not None:
                    try:
                        distance = float(distances[0][position])
                    except Exception:  # pragma: no cover - defensive
                        distance = 0.0
                    similarity = 1.0 / (1.0 + max(distance, 0.0))
                    results.append(
                        self._build_record(vector_id, entry, similarity=similarity)
                    )

            logger.info(f"Found {len(results)} similar vectors in FAISS")
            return results

        except Exception as e:
            logger.error(f"Error performing similarity search in FAISS: {e}")
            # Return empty results instead of raising an exception to make the code more robust
            return []

    def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector from the vector store.

        Args:
            vector_id: The ID of the vector to delete

        Returns:
            True if the vector was deleted, False if it was not found

        Raises:
            MemoryStoreError: If there is an error deleting the vector
        """
        try:
            # Check if the vector exists in metadata
            if vector_id not in self.metadata:
                logger.warning(f"Vector with ID {vector_id} not found for deletion")
                return False

            # Check if the vector is already marked as deleted
            if self.metadata[vector_id].get("is_deleted", False):
                logger.warning(f"Vector with ID {vector_id} is already deleted")
                return False

            # Mark the vector as deleted in metadata
            # Note: FAISS doesn't support direct deletion, so we mark it in metadata
            self.metadata[vector_id]["is_deleted"] = True

            # Save the metadata
            if not self._snapshots:
                self._save_metadata()

            logger.info(f"Marked vector with ID {vector_id} as deleted in FAISS")
            return True

        except Exception as e:
            logger.error(f"Error deleting vector from FAISS: {e}")
            raise MemoryStoreError(f"Error deleting vector: {e}")

    def get_collection_stats(self) -> VectorStoreStats:
        """Return statistics about the vector store collection."""

        try:
            active_vectors = sum(
                1
                for meta in self.metadata.values()
                if not meta.get("is_deleted", False)
            )

            stats: VectorStoreStats = {
                "collection_name": Path(self.base_path).name,
                "vector_count": active_vectors,
                "embedding_dimensions": self.dimension,
                "persist_directory": self.base_path,
                "metadata": {
                    "index_file": self.index_file,
                    "total_vectors_in_index": int(self.index.ntotal),
                },
            }

            logger.info("Retrieved collection statistics: %s", stats)
            return stats

        except Exception as exc:
            logger.error("Error getting collection statistics from FAISS: %s", exc)
            raise MemoryStoreError(f"Error getting collection statistics: {exc}")

    def get_all_vectors(self) -> list[MemoryVector]:
        """Return all stored vectors."""

        vectors: list[MemoryVector] = []
        for vid in list(self.metadata.keys()):
            vec = self.retrieve_vector(vid)
            if vec:
                vectors.append(vec)
        return vectors

    supports_transactions: bool = True
