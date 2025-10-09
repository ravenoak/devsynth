"""
ChromaDB adapter for vector storage.
"""

import json
import os
import uuid
from contextlib import contextmanager

try:
    import chromadb
except ImportError as e:  # pragma: no cover - optional dependency
    raise ImportError(
        "ChromaDBAdapter requires the 'chromadb' package. Install it with "
        "'pip install chromadb' or use the dev extras."
    ) from e
from datetime import datetime
from typing import Any, Dict, List, Optional

from devsynth.exceptions import MemoryStoreError

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...application.memory.dto import VectorStoreStats
from ...domain.interfaces.memory import VectorStore
from ...domain.models.memory import MemoryVector

logger = DevSynthLogger(__name__)


class ChromaDBAdapter(VectorStore[MemoryVector]):
    """ChromaDB implementation of the VectorStore interface."""

    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "devsynth_vectors",
        *,
        host: Optional[str] = None,
        port: int = 8000,
    ):
        """
        Initialize the ChromaDB adapter.

        Args:
            persist_directory: Directory where ChromaDB will store its data
            collection_name: Name of the ChromaDB collection to use
            host: Optional remote ChromaDB host
            port: Port for the remote ChromaDB server
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        # Track snapshots for basic transaction support. Each transaction
        # ID maps to a dictionary of vector data that can be restored if a
        # rollback is requested.  This lightweight approach keeps the adapter
        # self-contained while providing predictable behaviour during
        # synchronization tests where transactions are required.
        self._snapshots: Dict[str, Dict[str, Any]] = {}

        os.makedirs(persist_directory, exist_ok=True)

        try:
            if host:
                logger.info("Connecting to remote ChromaDB host %s:%s", host, port)
                self.client = chromadb.HttpClient(host=host, port=port)
            else:
                try:
                    self.client = chromadb.PersistentClient(path=persist_directory)
                    logger.info(
                        "Initialized ChromaDB client with persist directory: %s",
                        persist_directory,
                    )
                except Exception as exc:
                    # chromadb uses LMDB for persistence; when the dependency is
                    # missing fall back to an in-memory client so tests can run
                    # without the optional binary package.
                    logger.warning(
                        "Persistent ChromaDB unavailable (%s); "
                        "falling back to in-memory client",
                        exc,
                    )
                    self.client = chromadb.EphemeralClient()
        except Exception as exc:
            message = f"Failed to initialize ChromaDB client: {exc}"
            logger.error(message)
            raise MemoryStoreError(message)

        # Get or create the collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(
                "Using existing ChromaDB collection: %s",
                collection_name,
            )
        except Exception:
            # Collection doesn't exist, create it
            try:
                self.collection = self.client.create_collection(name=collection_name)
                logger.info(
                    "Created new ChromaDB collection: %s",
                    collection_name,
                )
            except Exception as exc:
                message = f"Failed to create ChromaDB collection: {exc}"
                logger.error(message)
                raise MemoryStoreError(message)

    # ------------------------------------------------------------------
    # Transaction helpers
    # ------------------------------------------------------------------
    def begin_transaction(self, transaction_id: Optional[str] = None) -> str:
        """Begin a new transaction and return its identifier.

        ChromaDB does not expose native transactional semantics, so we
        implement a simple snapshot mechanism.  When a transaction starts we
        capture all existing vectors so that they can be restored on rollback.

        Parameters
        ----------
        transaction_id:
            Optional identifier supplied by the caller.  If not provided a new
            UUID is generated.
        """

        tx_id = transaction_id or str(uuid.uuid4())
        if tx_id in self._snapshots:
            raise MemoryStoreError(f"Transaction {tx_id} already active")
        try:
            snapshot: Dict[str, Any] = {}
            result = self.collection.get(include=["embeddings", "metadatas"])
            for vid, emb, meta in zip(
                result.get("ids", []),
                result.get("embeddings", []),
                result.get("metadatas", []),
            ):
                snapshot[vid] = {"embedding": emb, "metadata": meta}
            self._snapshots[tx_id] = snapshot
            logger.debug("Began ChromaDB transaction %s", tx_id)
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Error beginning ChromaDB transaction %s: %s", tx_id, e)
            raise MemoryStoreError(f"Error beginning transaction {tx_id}: {e}")
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a previously started transaction."""

        if transaction_id not in self._snapshots:
            raise MemoryStoreError(
                f"Commit requested for unknown ChromaDB transaction {transaction_id}"
            )
        self._snapshots.pop(transaction_id, None)
        logger.debug("Committed ChromaDB transaction %s", transaction_id)
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction and restore the snapshot."""

        snapshot = self._snapshots.pop(transaction_id, None)
        if snapshot is None:
            raise MemoryStoreError(
                f"Rollback requested for unknown ChromaDB transaction {transaction_id}"
            )
        try:
            current = self.collection.get()
            if current.get("ids"):
                self.collection.delete(ids=current["ids"])
            if snapshot:
                self.collection.upsert(
                    ids=list(snapshot.keys()),
                    embeddings=[v["embedding"] for v in snapshot.values()],
                    metadatas=[v["metadata"] for v in snapshot.values()],
                )
            logger.debug("Rolled back ChromaDB transaction %s", transaction_id)
            return True
        except Exception as e:  # pragma: no cover - defensive
            logger.error(
                "Error rolling back ChromaDB transaction %s: %s", transaction_id, e
            )
            raise MemoryStoreError(
                f"Error rolling back transaction {transaction_id}: {e}"
            )

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` if ``transaction_id`` has an active snapshot."""

        return transaction_id in self._snapshots

    def prepare_commit(self, transaction_id: str) -> bool:
        """Validate that a transaction is ready to commit.

        The adapter maintains all write operations eagerly, so preparing a
        commit simply verifies that the transaction is active.

        Args:
            transaction_id: The transaction identifier to validate

        Returns:
            bool: ``True`` if the transaction is active

        Raises:
            MemoryStoreError: If no transaction with ``transaction_id`` exists
        """

        if not self.is_transaction_active(transaction_id):
            raise MemoryStoreError(
                f"Prepare requested for unknown ChromaDB transaction {transaction_id}"
            )
        return True

    # ------------------------------------------------------------------
    @contextmanager
    def transaction(self, transaction_id: Optional[str] = None):
        """Context manager providing transactional semantics.

        Parameters
        ----------
        transaction_id:
            Optional identifier supplied by the caller. When ``None`` a
            UUID-based identifier is generated.

        Yields
        ------
        str
            The transaction identifier for the active transaction.
        """

        tx_id = self.begin_transaction(transaction_id)
        try:
            yield tx_id
        except Exception:
            self.rollback_transaction(tx_id)
            raise
        else:
            self.prepare_commit(tx_id)
            self.commit_transaction(tx_id)

    def _serialize_metadata(self, vector: MemoryVector) -> Dict[str, Any]:
        """
        Serialize the vector metadata for storage in ChromaDB.

        Args:
            vector: The MemoryVector to serialize

        Returns:
            A dictionary of serialized metadata
        """
        # Convert created_at to ISO format string
        created_at_str = (
            vector.created_at.isoformat()
            if vector.created_at
            else datetime.now().isoformat()
        )

        # Create a serialized representation of the content and metadata
        serialized = {
            "content": vector.content,
            "metadata": vector.metadata,
            "created_at": created_at_str,
        }

        return {"vector_data": json.dumps(serialized)}

    def _deserialize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize metadata from ChromaDB.

        Args:
            metadata: The metadata from ChromaDB

        Returns:
            A dictionary containing deserialized content and metadata
        """
        if "vector_data" not in metadata:
            return {"content": None, "metadata": {}, "created_at": None}

        try:
            data = json.loads(metadata["vector_data"])
            return {
                "content": data.get("content"),
                "metadata": data.get("metadata", {}),
                "created_at": data.get("created_at"),
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize vector metadata: {e}")
            return {"content": None, "metadata": {}, "created_at": None}

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

            # Serialize metadata
            metadata = self._serialize_metadata(vector)

            # Store in ChromaDB
            self.collection.upsert(
                ids=[vector.id], embeddings=[vector.embedding], metadatas=[metadata]
            )

            logger.info(f"Stored vector with ID {vector.id} in ChromaDB")
            return vector.id
        except Exception as e:
            logger.error(f"Failed to store vector in ChromaDB: {e}")
            raise MemoryStoreError(f"Failed to store vector in ChromaDB: {e}")

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
            # Query ChromaDB for the vector
            result = self.collection.get(
                ids=[vector_id], include=["embeddings", "metadatas"]
            )

            # Check if the vector was found
            if not result["ids"] or not result["metadatas"]:
                logger.warning(f"Vector with ID {vector_id} not found in ChromaDB")
                return None

            # Extract the vector data
            metadata = result["metadatas"][0]
            embedding = result["embeddings"][0]

            # Deserialize the metadata
            deserialized = self._deserialize_metadata(metadata)

            # Create a MemoryVector
            created_at = (
                datetime.fromisoformat(deserialized["created_at"])
                if deserialized["created_at"]
                else None
            )

            vector = MemoryVector(
                id=vector_id,
                content=deserialized["content"],
                embedding=embedding,
                metadata=deserialized["metadata"],
                created_at=created_at,
            )

            logger.info(f"Retrieved vector with ID {vector_id} from ChromaDB")
            return vector
        except Exception as e:
            logger.error(f"Failed to retrieve vector from ChromaDB: {e}")
            raise MemoryStoreError(f"Failed to retrieve vector from ChromaDB: {e}")

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
            # Perform the similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["embeddings", "metadatas", "distances"],
            )

            # Check if any results were found
            if not results["ids"] or not results["ids"][0]:
                logger.info("No similar vectors found in ChromaDB")
                return []

            # Extract the results
            vectors = []
            for i, vector_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                embedding = results["embeddings"][0][i]

                # Deserialize the metadata
                deserialized = self._deserialize_metadata(metadata)

                # Create a MemoryVector
                created_at = (
                    datetime.fromisoformat(deserialized["created_at"])
                    if deserialized["created_at"]
                    else None
                )

                vector = MemoryVector(
                    id=vector_id,
                    content=deserialized["content"],
                    embedding=embedding,
                    metadata=deserialized["metadata"],
                    created_at=created_at,
                )

                vectors.append(vector)

            logger.info(f"Found {len(vectors)} similar vectors in ChromaDB")
            return vectors
        except Exception as e:
            logger.error(f"Failed to perform similarity search in ChromaDB: {e}")
            raise MemoryStoreError(
                f"Failed to perform similarity search in ChromaDB: {e}"
            )

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
            # Check if the vector exists
            result = self.collection.get(ids=[vector_id])
            if not result["ids"]:
                logger.warning(f"Vector with ID {vector_id} not found for deletion")
                return False

            # Delete the vector
            self.collection.delete(ids=[vector_id])

            logger.info(f"Deleted vector with ID {vector_id} from ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector from ChromaDB: {e}")
            raise MemoryStoreError(f"Failed to delete vector from ChromaDB: {e}")

    def flush(self) -> None:
        """Flush pending changes to the persistence layer."""

        try:
            if hasattr(self.client, "persist"):
                self.client.persist()
        except Exception:
            logger.debug("ChromaDB flush failed", exc_info=True)

    def get_collection_stats(self) -> VectorStoreStats:
        """Return a typed view of the collection statistics."""

        try:
            result = self.collection.get(include=["embeddings"])

            vector_count = len(result["ids"]) if result["ids"] else 0

            embedding_dimensions = 0
            if vector_count > 0 and len(result["embeddings"]) > 0:
                first_embedding = result["embeddings"][0]
                if hasattr(first_embedding, "shape"):
                    embedding_dimensions = first_embedding.shape[0]
                else:
                    embedding_dimensions = len(first_embedding)

            stats: VectorStoreStats = {
                "collection_name": self.collection_name,
                "vector_count": vector_count,
                "embedding_dimensions": embedding_dimensions,
                "persist_directory": self.persist_directory,
            }

            logger.info("Retrieved collection statistics: %s", stats)
            return stats
        except Exception as exc:
            logger.error("Failed to get collection statistics from ChromaDB: %s", exc)
            raise MemoryStoreError(
                f"Failed to get collection statistics from ChromaDB: {exc}"
            )

    def get_all_vectors(self) -> List[MemoryVector]:
        """Return all stored :class:`MemoryVector` objects."""

        try:
            result = self.collection.get(include=["embeddings", "metadatas"])
            vectors = []
            for vid, emb, meta in zip(
                result["ids"], result["embeddings"], result["metadatas"]
            ):
                deserialized = self._deserialize_metadata(meta)
                created = (
                    datetime.fromisoformat(deserialized["created_at"])
                    if deserialized["created_at"]
                    else None
                )
                vectors.append(
                    MemoryVector(
                        id=vid,
                        content=deserialized["content"],
                        embedding=emb,
                        metadata=deserialized["metadata"],
                        created_at=created,
                    )
                )
            logger.info("Retrieved %s vectors from ChromaDB", len(vectors))
            return vectors
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Failed to get all vectors from ChromaDB: %s", e)
            return []
