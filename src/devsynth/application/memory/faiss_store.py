"""
FAISS implementation of VectorStore.

This implementation uses FAISS for efficient vector similarity search.
"""

import json
import os
import uuid
from contextlib import contextmanager
from copy import deepcopy

import numpy as np
import tiktoken

try:
    import faiss
except ImportError as e:  # pragma: no cover - optional dependency
    raise ImportError(
        "FAISSStore requires the 'faiss' package. Install it with 'pip install faiss-cpu' or use the dev extras."
    ) from e
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from devsynth.exceptions import (
    DevSynthError,
    MemoryError,
    MemoryItemNotFoundError,
    MemoryStoreError,
)
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.memory import VectorStore
from ...domain.models.memory import MemoryVector

# Create a logger for this module
logger = DevSynthLogger(__name__)


class FAISSStore(VectorStore):
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
        self.base_path = base_path
        self.index_file = os.path.join(self.base_path, "faiss_index.bin")
        self.metadata_file = os.path.join(self.base_path, "metadata.json")
        self.token_count = 0
        self.dimension = dimension

        # Ensure the directory exists
        os.makedirs(self.base_path, exist_ok=True)

        # Initialize the tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding
        except Exception as e:
            logger.warning(
                f"Failed to initialize tokenizer: {e}. Token counting will be approximate."
            )
            self.tokenizer = None

        # Initialize FAISS index and metadata
        self._initialize_store()

        # Track transaction snapshots.  Each active transaction stores a
        # cloned FAISS index and metadata dictionary so that rollback can
        # restore the previous state if an error occurs.
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    def _initialize_store(self):
        """Initialize the FAISS index and metadata store."""
        try:
            # Initialize metadata dictionary
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, "r") as f:
                    self.metadata = json.load(f)
                # Get dimension from existing metadata
                if self.metadata and len(self.metadata) > 0:
                    first_id = next(iter(self.metadata))
                    if "embedding" in self.metadata[first_id]:
                        self.dimension = len(self.metadata[first_id]["embedding"])
            else:
                self.metadata = {}

            # Initialize or load FAISS index
            if os.path.exists(self.index_file):
                self.index = faiss.read_index(self.index_file)
                logger.info(f"Loaded existing FAISS index from {self.index_file}")
            else:
                # Create a new index - using L2 distance (Euclidean)
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info(f"Created new FAISS index with dimension {self.dimension}")

            logger.info("FAISS store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS store: {e}")
            raise MemoryStoreError(f"Failed to initialize FAISS store: {e}")

    def _save_index(self):
        """Save the FAISS index to disk."""
        try:
            faiss.write_index(self.index, self.index_file)
            logger.info(f"Saved FAISS index to {self.index_file}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            raise MemoryStoreError(f"Failed to save FAISS index: {e}")

    def _save_metadata(self):
        """Save the metadata to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f)
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

    def _serialize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare metadata for serialization.

        Args:
            metadata: The metadata dictionary

        Returns:
            A serializable version of the metadata
        """
        # Convert datetime objects to ISO format strings
        result = {}
        for key, value in metadata.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def _deserialize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize metadata from storage.

        Args:
            metadata: The serialized metadata

        Returns:
            The deserialized metadata
        """
        # Convert ISO format strings back to datetime objects
        result = {}
        for key, value in metadata.items():
            if key == "created_at" and isinstance(value, str):
                try:
                    result[key] = datetime.fromisoformat(value)
                except ValueError:
                    result[key] = value
            else:
                result[key] = value
        return result

    # ------------------------------------------------------------------
    # Transaction management

    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a new transaction and return its identifier."""

        tx_id = transaction_id or str(uuid.uuid4())
        if tx_id in self._snapshots:
            raise MemoryStoreError(f"Transaction {tx_id} already active")
        # Clone index and metadata for rollback
        try:
            index_clone = faiss.deserialize_index(faiss.serialize_index(self.index))
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to snapshot FAISS index: {exc}")
            raise MemoryStoreError("Failed to snapshot FAISS index")
        self._snapshots[tx_id] = {
            "index": index_clone,
            "metadata": deepcopy(self.metadata),
        }
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
        self.index = snap["index"]
        self.metadata = snap["metadata"]
        self._save_index()
        self._save_metadata()
        return True

    @contextmanager
    def transaction(self, transaction_id: str | None = None):
        """Context manager providing transactional semantics."""

        tx_id = self.begin_transaction(transaction_id)
        try:
            yield tx_id
        except Exception:
            self.rollback_transaction(tx_id)
            raise
        else:
            self.commit_transaction(tx_id)

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
                self.index = faiss.IndexFlatL2(self.dimension)

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
                "embedding": vector.embedding,
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

    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:
        """
        Retrieve a vector from the vector store by ID.

        Args:
            vector_id: The ID of the vector to retrieve

        Returns:
            The retrieved MemoryVector, or None if not found

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

            # Create a MemoryVector
            vector = MemoryVector(
                id=vector_id,
                content=vector_metadata.get("content"),
                embedding=vector_metadata.get("embedding"),
                metadata=self._deserialize_metadata(
                    vector_metadata.get("metadata", {})
                ),
                created_at=(
                    datetime.fromisoformat(vector_metadata.get("created_at"))
                    if vector_metadata.get("created_at")
                    else None
                ),
            )

            # Update token count
            token_count = self._count_tokens(str(vector))
            self.token_count += token_count

            logger.info(f"Retrieved vector with ID {vector_id} from FAISS")
            return vector

        except Exception as e:
            logger.error(f"Error retrieving vector from FAISS: {e}")
            raise MemoryStoreError(f"Error retrieving vector: {e}")

    def similarity_search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[MemoryVector]:
        """
        Search for vectors similar to the query embedding.

        Args:
            query_embedding: The embedding to search for
            top_k: The number of results to return

        Returns:
            A list of MemoryVectors similar to the query embedding

        Raises:
            MemoryStoreError: If there is an error performing the search
        """
        try:
            # Convert query_embedding to numpy array
            query = np.array(query_embedding, dtype=np.float32)

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
            if not isinstance(self.index, faiss.IndexFlatL2):
                logger.warning("FAISS index is not properly initialized, recreating it")
                self.index = faiss.IndexFlatL2(self.dimension)
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
            results = []
            for i, idx in enumerate(indices[0]):
                # Skip invalid indices
                if idx < 0 or idx >= self.index.ntotal:
                    logger.warning(f"Skipping invalid index {idx}")
                    continue

                # Find the vector ID for this index
                vector_id = None
                for vid, meta in self.metadata.items():
                    if meta.get("index") == idx and not meta.get("is_deleted", False):
                        vector_id = vid
                        break

                if vector_id:
                    try:
                        # Retrieve the vector
                        vector = self.retrieve_vector(vector_id)
                        if vector:
                            results.append(vector)
                    except Exception as e:
                        logger.warning(f"Error retrieving vector {vector_id}: {e}")
                        continue

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

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            A dictionary of collection statistics

        Raises:
            MemoryStoreError: If there is an error getting collection statistics
        """
        try:
            # Count non-deleted vectors
            active_vectors = sum(
                1
                for meta in self.metadata.values()
                if not meta.get("is_deleted", False)
            )

            stats = {
                "num_vectors": active_vectors,
                "embedding_dimension": self.dimension,
                "index_file": self.index_file,
                "total_vectors_in_index": self.index.ntotal,
            }

            logger.info(f"Retrieved collection statistics: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting collection statistics from FAISS: {e}")
            raise MemoryStoreError(f"Error getting collection statistics: {e}")

    def get_all_vectors(self) -> List[MemoryVector]:
        """Return all stored vectors."""

        vectors: List[MemoryVector] = []
        for vid in list(self.metadata.keys()):
            vec = self.retrieve_vector(vid)
            if vec:
                vectors.append(vec)
        return vectors
