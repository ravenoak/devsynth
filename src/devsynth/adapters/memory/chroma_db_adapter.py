
"""
ChromaDB adapter for vector storage.
"""

import os
import json
import uuid
try:
    import chromadb
except ImportError as e:  # pragma: no cover - optional dependency
    raise ImportError(
        "ChromaDBAdapter requires the 'chromadb' package. Install it with 'pip install chromadb' or use the dev extras."
    ) from e
import numpy as np
from typing import Any, Dict, List, Optional, Union
from ...domain.interfaces.memory import VectorStore
from ...domain.models.memory import MemoryVector
from datetime import datetime

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError, MemoryStoreError, MemoryItemNotFoundError

logger = DevSynthLogger(__name__)

class ChromaDBAdapter(VectorStore):
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

        os.makedirs(persist_directory, exist_ok=True)

        try:
            if host:
                logger.info("Connecting to remote ChromaDB host %s:%s", host, port)
                self.client = chromadb.HttpClient(host=host, port=port)
            else:
                self.client = chromadb.PersistentClient(path=persist_directory)
                logger.info(
                    f"Initialized ChromaDB client with persist directory: {persist_directory}"
                )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise MemoryStoreError(f"Failed to initialize ChromaDB client: {e}")

        # Get or create the collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Using existing ChromaDB collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            try:
                self.collection = self.client.create_collection(name=collection_name)
                logger.info(f"Created new ChromaDB collection: {collection_name}")
            except Exception as e:
                logger.error(f"Failed to create ChromaDB collection: {e}")
                raise MemoryStoreError(f"Failed to create ChromaDB collection: {e}")

    def _serialize_metadata(self, vector: MemoryVector) -> Dict[str, Any]:
        """
        Serialize the vector metadata for storage in ChromaDB.

        Args:
            vector: The MemoryVector to serialize

        Returns:
            A dictionary of serialized metadata
        """
        # Convert created_at to ISO format string
        created_at_str = vector.created_at.isoformat() if vector.created_at else datetime.now().isoformat()

        # Create a serialized representation of the content and metadata
        serialized = {
            "content": vector.content,
            "metadata": vector.metadata,
            "created_at": created_at_str
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
                "created_at": data.get("created_at")
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
                ids=[vector.id],
                embeddings=[vector.embedding],
                metadatas=[metadata]
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
            result = self.collection.get(ids=[vector_id], include=["embeddings", "metadatas"])

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
            created_at = datetime.fromisoformat(deserialized["created_at"]) if deserialized["created_at"] else None

            vector = MemoryVector(
                id=vector_id,
                content=deserialized["content"],
                embedding=embedding,
                metadata=deserialized["metadata"],
                created_at=created_at
            )

            logger.info(f"Retrieved vector with ID {vector_id} from ChromaDB")
            return vector
        except Exception as e:
            logger.error(f"Failed to retrieve vector from ChromaDB: {e}")
            raise MemoryStoreError(f"Failed to retrieve vector from ChromaDB: {e}")

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[MemoryVector]:
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
                include=["embeddings", "metadatas", "distances"]
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
                created_at = datetime.fromisoformat(deserialized["created_at"]) if deserialized["created_at"] else None

                vector = MemoryVector(
                    id=vector_id,
                    content=deserialized["content"],
                    embedding=embedding,
                    metadata=deserialized["metadata"],
                    created_at=created_at
                )

                vectors.append(vector)

            logger.info(f"Found {len(vectors)} similar vectors in ChromaDB")
            return vectors
        except Exception as e:
            logger.error(f"Failed to perform similarity search in ChromaDB: {e}")
            raise MemoryStoreError(f"Failed to perform similarity search in ChromaDB: {e}")

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

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            A dictionary of collection statistics

        Raises:
            MemoryStoreError: If there is an error getting collection statistics
        """
        try:
            # Get all vectors to calculate statistics
            result = self.collection.get(include=["embeddings"])

            # Calculate statistics
            num_vectors = len(result["ids"]) if result["ids"] else 0

            # Calculate embedding dimension if vectors exist
            embedding_dimension = 0
            if num_vectors > 0 and len(result["embeddings"]) > 0:
                # Handle the case where embeddings might be a numpy array
                first_embedding = result["embeddings"][0]
                if hasattr(first_embedding, "shape"):
                    # It's a numpy array
                    embedding_dimension = first_embedding.shape[0]
                else:
                    # It's a list
                    embedding_dimension = len(first_embedding)

            stats = {
                "collection_name": self.collection_name,
                "num_vectors": num_vectors,
                "embedding_dimension": embedding_dimension,
                "persist_directory": self.persist_directory
            }

            logger.info(f"Retrieved collection statistics: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to get collection statistics from ChromaDB: {e}")
            raise MemoryStoreError(f"Failed to get collection statistics from ChromaDB: {e}")
