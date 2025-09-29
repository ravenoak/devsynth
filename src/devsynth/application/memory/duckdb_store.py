"""
DuckDB implementation of MemoryStore and VectorStore.

This implementation uses DuckDB with its vector similarity search extension
to store and retrieve memory items and vectors. It also supports HNSW indexing
for faster vector similarity search.
"""

import json
import os
import uuid

import numpy as np
import tiktoken

try:  # pragma: no cover - optional dependency
    import duckdb  # type: ignore
except Exception:  # pragma: no cover - gracefully handle missing duckdb
    duckdb = None  # type: ignore[assignment]
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from devsynth.core import feature_flags
from devsynth.exceptions import (
    DevSynthError,
    MemoryError,
    MemoryItemNotFoundError,
    MemoryStoreError,
)
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.memory import MemoryStore, VectorStore
from ...domain.models.memory import MemoryItem, MemoryType, MemoryVector
from .dto import MemoryMetadata
from .metadata_serialization import dumps as metadata_dumps, loads as metadata_loads

# Create a logger for this module
logger = DevSynthLogger(__name__)


class DuckDBStore(MemoryStore, VectorStore):
    """
    DuckDB implementation of the MemoryStore and VectorStore interfaces.

    This class uses DuckDB with its vector similarity search extension to store
    and retrieve memory items and vectors. It also supports HNSW indexing for
    faster vector similarity search.
    """

    def __init__(
        self,
        base_path: str,
        enable_hnsw: bool = False,
        hnsw_config: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize a DuckDBStore.

        Args:
            base_path: Base path for storing the DuckDB database file
            enable_hnsw: Whether to enable HNSW indexing for vector similarity search
            hnsw_config: Configuration parameters for HNSW indexing
                - M: Number of bi-directional links created for each node (default: 12)
                - efConstruction: Size of the dynamic list for nearest neighbors during index construction (default: 100)
                - efSearch: Size of the dynamic list for nearest neighbors during search (default: 50)
        """
        if duckdb is None:  # pragma: no cover - runtime check for optional dep
            raise ImportError(
                "DuckDBStore requires the 'duckdb' package. Install it with 'pip install duckdb' or use the dev extras."
            )

        self.base_path = base_path
        self.db_file = os.path.join(self.base_path, "memory.duckdb")
        self.token_count = 0
        self.enable_hnsw = enable_hnsw
        self.vector_extension_available = False

        # Set default HNSW configuration if not provided
        if hnsw_config is None:
            self.hnsw_config = {"M": 12, "efConstruction": 100, "efSearch": 50}
        else:
            self.hnsw_config = hnsw_config

        # Ensure the directory exists
        os.makedirs(self.base_path, exist_ok=True)

        # Initialize DuckDB connection
        self.conn = duckdb.connect(self.db_file)

        # Initialize the tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding
        except Exception as e:
            logger.warning(
                f"Failed to initialize tokenizer: {e}. Token counting will be approximate."
            )
            self.tokenizer = None

        # Initialize database schema
        self._initialize_schema()

    def _initialize_schema(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            # Load the vector extension
            try:
                self.conn.execute("INSTALL vector; LOAD vector;")
                self.vector_extension_available = True
            except Exception as e:
                logger.warning(
                    f"Failed to load vector extension: {e}. Vector similarity search will be limited."
                )
                self.vector_extension_available = False

            # Create memory_items table if it doesn't exist
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id VARCHAR PRIMARY KEY,
                    content VARCHAR,
                    memory_type VARCHAR,
                    metadata VARCHAR,  -- JSON string
                    created_at VARCHAR
                );
            """
            )

            # Create memory_vectors table if it doesn't exist
            if self.vector_extension_available:
                self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_vectors (
                        id VARCHAR PRIMARY KEY,
                        content VARCHAR,
                        embedding FLOAT[],  -- Vector of floats
                        metadata VARCHAR,  -- JSON string
                        created_at VARCHAR
                    );
                """
                )
            else:
                # Fallback for testing without vector extension
                self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_vectors (
                        id VARCHAR PRIMARY KEY,
                        content VARCHAR,
                        embedding VARCHAR,  -- Store as JSON string for testing
                        metadata VARCHAR,  -- JSON string
                        created_at VARCHAR
                    );
                """
                )

            # Configure HNSW parameters if enabled and vector extension is available
            if self.enable_hnsw and self.vector_extension_available:
                try:
                    if feature_flags.experimental_enabled():
                        # Enable experimental persistence for HNSW indexes
                        self.conn.execute(
                            "SET hnsw_enable_experimental_persistence = true;"
                        )

                    # Set HNSW parameters
                    self.conn.execute(f"SET hnsw_M = {self.hnsw_config['M']};")
                    self.conn.execute(
                        f"SET hnsw_efConstruction = {self.hnsw_config['efConstruction']};"
                    )
                    self.conn.execute(
                        f"SET hnsw_efSearch = {self.hnsw_config['efSearch']};"
                    )

                    logger.info(
                        f"HNSW indexing enabled with parameters: {self.hnsw_config}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to configure HNSW parameters: {e}. HNSW indexing will be disabled."
                    )
                    self.enable_hnsw = False

            logger.info("DuckDB schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DuckDB schema: {e}")
            raise MemoryStoreError(
                "Failed to initialize DuckDB schema",
                store_type="duckdb",
                operation="initialize_schema",
                original_error=e,
            )

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

    def _serialize_metadata(self, metadata: MemoryMetadata | None) -> str:
        """Serialize metadata to a JSON string using typed helpers."""

        return metadata_dumps(metadata)

    def _deserialize_metadata(self, metadata_str: str | None) -> MemoryMetadata:
        """Deserialize a JSON string into ``MemoryMetadata`` values."""

        try:
            return metadata_loads(metadata_str)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to deserialize metadata: %s", metadata_str)
            return {}

    def store(self, item: MemoryItem) -> str:
        """
        Store an item in memory and return its ID.

        Args:
            item: The MemoryItem to store

        Returns:
            The ID of the stored item

        Raises:
            MemoryStoreError: If the item cannot be stored
        """
        try:
            # Generate an ID if not provided
            if not item.id:
                item.id = str(uuid.uuid4())

            # Serialize metadata
            metadata_json = self._serialize_metadata(item.metadata)

            # Convert created_at to ISO format string
            created_at_str = (
                item.created_at.isoformat()
                if item.created_at
                else datetime.now().isoformat()
            )

            # Store in DuckDB
            self.conn.execute(
                """
                INSERT OR REPLACE INTO memory_items (id, content, memory_type, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    item.id,
                    item.content,
                    item.memory_type.value if item.memory_type else None,
                    metadata_json,
                    created_at_str,
                ),
            )

            # Update token count
            token_count = self._count_tokens(str(item))
            self.token_count += token_count

            logger.info(f"Stored item with ID {item.id} in DuckDB")
            return item.id

        except Exception as e:
            logger.error(f"Failed to store item in DuckDB: {e}")
            raise MemoryStoreError(
                "Failed to store item",
                store_type="duckdb",
                operation="store",
                original_error=e,
            )

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve an item from memory by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved MemoryItem, or None if not found

        Raises:
            MemoryStoreError: If there is an error retrieving the item
        """
        try:
            # Query DuckDB for the item
            result = self.conn.execute(
                """
                SELECT id, content, memory_type, metadata, created_at
                FROM memory_items
                WHERE id = ?
            """,
                (item_id,),
            ).fetchone()

            # Check if the item was found
            if not result:
                logger.warning(f"Item with ID {item_id} not found in DuckDB")
                return None

            # Deserialize metadata
            metadata = self._deserialize_metadata(result[3])

            # Convert memory_type string to enum
            memory_type = MemoryType(result[2]) if result[2] else None

            # Convert created_at string to datetime
            created_at = datetime.fromisoformat(result[4]) if result[4] else None

            # Create a MemoryItem
            item = MemoryItem(
                id=result[0],
                content=result[1],
                memory_type=memory_type,
                metadata=metadata,
                created_at=created_at,
            )

            # Update token count
            token_count = self._count_tokens(str(item))
            self.token_count += token_count

            logger.info(f"Retrieved item with ID {item_id} from DuckDB")
            return item

        except Exception as e:
            logger.error(f"Error retrieving item from DuckDB: {e}")
            raise MemoryStoreError(
                "Error retrieving item",
                store_type="duckdb",
                operation="retrieve",
                original_error=e,
            )

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Search for items in memory matching the query.

        Args:
            query: Dictionary of search criteria

        Returns:
            List of matching memory items

        Raises:
            MemoryStoreError: If the search operation fails
        """
        try:
            logger.info(f"Searching items in DuckDB with query: {query}")

            # Build the SQL query
            sql = "SELECT id, content, memory_type, metadata, created_at FROM memory_items WHERE 1=1"
            params = []

            # Add query conditions
            for key, value in query.items():
                if key == "memory_type" and isinstance(value, MemoryType):
                    sql += " AND memory_type = ?"
                    params.append(value.value)
                elif key == "content" and isinstance(value, str):
                    sql += " AND content LIKE ?"
                    params.append(f"%{value}%")
                elif key.startswith("metadata."):
                    # For metadata fields, we need to use JSON functions
                    field = key.split(".", 1)[1]
                    # When searching for string values, we need to wrap them in quotes for JSON comparison
                    if isinstance(value, str):
                        sql += f" AND json_extract(metadata, '$.{field}') = ?"
                        # Properly format string value for JSON comparison
                        params.append(json.dumps(value))
                    else:
                        sql += f" AND json_extract(metadata, '$.{field}') = ?"
                        params.append(value)

            # Execute the query
            results = self.conn.execute(sql, params).fetchall()

            # Convert results to MemoryItems
            items = []
            for result in results:
                # Deserialize metadata
                metadata = self._deserialize_metadata(result[3])

                # Convert memory_type string to enum
                memory_type = MemoryType(result[2]) if result[2] else None

                # Convert created_at string to datetime
                created_at = datetime.fromisoformat(result[4]) if result[4] else None

                # Create a MemoryItem
                item = MemoryItem(
                    id=result[0],
                    content=result[1],
                    memory_type=memory_type,
                    metadata=metadata,
                    created_at=created_at,
                )

                items.append(item)

            # Update token count
            if items:
                token_count = sum(self._count_tokens(str(item)) for item in items)
                self.token_count += token_count

            logger.info(f"Found {len(items)} matching items in DuckDB")
            return items

        except Exception as e:
            logger.error(f"Error searching items in DuckDB: {e}")
            raise MemoryStoreError(
                "Error searching items",
                store_type="duckdb",
                operation="search",
                original_error=e,
            )

    def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False if it was not found

        Raises:
            MemoryStoreError: If the delete operation fails
        """
        try:
            # Check if the item exists
            result = self.conn.execute(
                """
                SELECT id FROM memory_items WHERE id = ?
            """,
                (item_id,),
            ).fetchone()

            if not result:
                logger.warning(f"Item with ID {item_id} not found for deletion")
                return False

            # Delete the item
            self.conn.execute(
                """
                DELETE FROM memory_items WHERE id = ?
            """,
                (item_id,),
            )

            logger.info(f"Deleted item with ID {item_id} from DuckDB")
            return True

        except Exception as e:
            logger.error(f"Error deleting item from DuckDB: {e}")
            raise MemoryStoreError(
                "Error deleting item",
                store_type="duckdb",
                operation="delete",
                original_error=e,
            )

    def get_token_usage(self) -> int:
        """
        Get the current token usage estimate.

        Returns:
            The estimated token usage
        """
        return self.token_count

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
            metadata_json = self._serialize_metadata(vector.metadata)

            # Convert created_at to ISO format string
            created_at_str = (
                vector.created_at.isoformat()
                if vector.created_at
                else datetime.now().isoformat()
            )

            # Convert embedding to a list if it's a numpy array
            embedding = vector.embedding
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()

            # Store in DuckDB
            if self.vector_extension_available:
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO memory_vectors (id, content, embedding, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        vector.id,
                        vector.content,
                        embedding,
                        metadata_json,
                        created_at_str,
                    ),
                )
            else:
                # Fallback for testing without vector extension
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO memory_vectors (id, content, embedding, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        vector.id,
                        vector.content,
                        json.dumps(embedding),  # Store as JSON string for testing
                        metadata_json,
                        created_at_str,
                    ),
                )

            # Create HNSW index if enabled, vector extension is available, and index not already created
            if self.enable_hnsw and self.vector_extension_available:
                try:
                    # Check if index already exists
                    result = self.conn.execute(
                        """
                        SELECT * FROM duckdb_indexes()
                        WHERE index_type = 'hnsw'
                    """
                    ).fetchall()

                    if len(result) == 0:
                        # Create HNSW index on the embedding column
                        self.conn.execute(
                            """
                            CREATE INDEX IF NOT EXISTS memory_vectors_hnsw_idx
                            ON memory_vectors USING HNSW(embedding);
                        """
                        )
                        logger.info("Created HNSW index on memory_vectors table")
                except Exception as e:
                    logger.warning(f"Failed to create HNSW index: {e}")

            logger.info(f"Stored vector with ID {vector.id} in DuckDB")
            return vector.id

        except Exception as e:
            logger.error(f"Failed to store vector in DuckDB: {e}")
            raise MemoryStoreError(
                "Failed to store vector",
                store_type="duckdb",
                operation="store_vector",
                original_error=e,
            )

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
            # Query DuckDB for the vector
            result = self.conn.execute(
                """
                SELECT id, content, embedding, metadata, created_at
                FROM memory_vectors
                WHERE id = ?
            """,
                (vector_id,),
            ).fetchone()

            # Check if the vector was found
            if not result:
                logger.warning(f"Vector with ID {vector_id} not found in DuckDB")
                return None

            # Deserialize metadata
            metadata = self._deserialize_metadata(result[3])

            # Convert created_at string to datetime
            created_at = datetime.fromisoformat(result[4]) if result[4] else None

            # Parse embedding if needed
            embedding = result[2]
            if not self.vector_extension_available and isinstance(embedding, str):
                embedding = json.loads(embedding)

            # Create a MemoryVector
            vector = MemoryVector(
                id=result[0],
                content=result[1],
                embedding=embedding,
                metadata=metadata,
                created_at=created_at,
            )

            logger.info(f"Retrieved vector with ID {vector_id} from DuckDB")
            return vector

        except Exception as e:
            logger.error(f"Error retrieving vector from DuckDB: {e}")
            raise MemoryStoreError(
                "Error retrieving vector",
                store_type="duckdb",
                operation="retrieve_vector",
                original_error=e,
            )

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
            # Convert query_embedding to a list if it's a numpy array
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()

            # Use DuckDB's vector similarity search if vector extension is available
            if self.vector_extension_available:
                # If HNSW is enabled, the index will be used automatically
                results = self.conn.execute(
                    """
                    SELECT id, content, embedding, metadata, created_at,
                           vector_distance(embedding, ?) as distance
                    FROM memory_vectors
                    ORDER BY distance ASC
                    LIMIT ?
                """,
                    (query_embedding, top_k),
                ).fetchall()

                # Convert results to MemoryVectors
                vectors = []
                for result in results:
                    # Deserialize metadata
                    metadata = self._deserialize_metadata(result[3])

                    # Convert created_at string to datetime
                    created_at = (
                        datetime.fromisoformat(result[4]) if result[4] else None
                    )

                    # Create a MemoryVector
                    vector = MemoryVector(
                        id=result[0],
                        content=result[1],
                        embedding=result[2],
                        metadata=metadata,
                        created_at=created_at,
                    )

                    vectors.append(vector)

                search_type = "HNSW index" if self.enable_hnsw else "linear scan"
                logger.info(
                    f"Found {len(vectors)} similar vectors in DuckDB using {search_type}"
                )
            else:
                # Fallback for testing without vector extension
                # Get all vectors and compute distances in Python
                results = self.conn.execute(
                    """
                    SELECT id, content, embedding, metadata, created_at
                    FROM memory_vectors
                """
                ).fetchall()

                # Compute distances and sort
                vectors_with_distances = []
                for result in results:
                    # Deserialize metadata
                    metadata = self._deserialize_metadata(result[3])

                    # Convert created_at string to datetime
                    created_at = (
                        datetime.fromisoformat(result[4]) if result[4] else None
                    )

                    # Parse embedding from JSON string
                    embedding = json.loads(result[2])

                    # Compute Euclidean distance
                    distance = (
                        sum((a - b) ** 2 for a, b in zip(embedding, query_embedding))
                        ** 0.5
                    )

                    # Create a MemoryVector
                    vector = MemoryVector(
                        id=result[0],
                        content=result[1],
                        embedding=embedding,
                        metadata=metadata,
                        created_at=created_at,
                    )

                    vectors_with_distances.append((vector, distance))

                # Sort by distance and take top_k
                vectors_with_distances.sort(key=lambda x: x[1])
                vectors = [v for v, _ in vectors_with_distances[:top_k]]

                logger.info(
                    f"Found {len(vectors)} similar vectors in DuckDB using Python fallback (vector extension not available)"
                )

            return vectors

        except Exception as e:
            logger.error(f"Error performing similarity search in DuckDB: {e}")
            raise MemoryStoreError(
                "Error performing similarity search",
                store_type="duckdb",
                operation="similarity_search",
                original_error=e,
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
            result = self.conn.execute(
                """
                SELECT id FROM memory_vectors WHERE id = ?
            """,
                (vector_id,),
            ).fetchone()

            if not result:
                logger.warning(f"Vector with ID {vector_id} not found for deletion")
                return False

            # Delete the vector
            self.conn.execute(
                """
                DELETE FROM memory_vectors WHERE id = ?
            """,
                (vector_id,),
            )

            logger.info(f"Deleted vector with ID {vector_id} from DuckDB")
            return True

        except Exception as e:
            logger.error(f"Error deleting vector from DuckDB: {e}")
            raise MemoryStoreError(
                "Error deleting vector",
                store_type="duckdb",
                operation="delete_vector",
                original_error=e,
            )

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            A dictionary of collection statistics

        Raises:
            MemoryStoreError: If there is an error getting collection statistics
        """
        try:
            # Get the number of vectors
            num_vectors = self.conn.execute(
                """
                SELECT COUNT(*) FROM memory_vectors
            """
            ).fetchone()[0]

            # Get the embedding dimension (from the first vector if available)
            embedding_dimension = 0
            if num_vectors > 0:
                first_vector = self.conn.execute(
                    """
                    SELECT embedding FROM memory_vectors LIMIT 1
                """
                ).fetchone()

                if first_vector and first_vector[0]:
                    if self.vector_extension_available:
                        embedding_dimension = len(first_vector[0])
                    else:
                        # Parse embedding from JSON string
                        embedding = json.loads(first_vector[0])
                        embedding_dimension = len(embedding)

            # Check if HNSW index exists
            hnsw_index_exists = False
            if self.enable_hnsw and self.vector_extension_available:
                try:
                    result = self.conn.execute(
                        """
                        SELECT * FROM duckdb_indexes()
                        WHERE index_type = 'hnsw'
                    """
                    ).fetchall()
                    hnsw_index_exists = len(result) > 0
                except Exception:
                    hnsw_index_exists = False

            stats = {
                "num_vectors": num_vectors,
                "embedding_dimension": embedding_dimension,
                "database_file": self.db_file,
                "vector_extension_available": self.vector_extension_available,
                "hnsw_enabled": self.enable_hnsw,
                "hnsw_index_exists": hnsw_index_exists,
            }

            # Add HNSW configuration if enabled
            if self.enable_hnsw:
                stats["hnsw_config"] = self.hnsw_config

            logger.info(f"Retrieved collection statistics: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting collection statistics from DuckDB: {e}")
            raise MemoryStoreError(
                "Error getting collection statistics",
                store_type="duckdb",
                operation="get_collection_stats",
                original_error=e,
            )
