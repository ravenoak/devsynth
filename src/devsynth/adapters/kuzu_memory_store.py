"""Adapter for ``KuzuStore`` integrating provider embeddings."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from devsynth.adapters.provider_system import ProviderError, embed
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.config import settings as settings_module
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryVector
from devsynth.exceptions import MemoryStoreError
from devsynth.logging_setup import DevSynthLogger

try:  # pragma: no cover - optional dependency
    from chromadb.utils import embedding_functions
except ImportError:  # pragma: no cover - optional dependency
    embedding_functions = None

logger = DevSynthLogger(__name__)


def _is_kuzu_available() -> bool:
    """Return True if the Kuzu dependency is available."""
    if os.environ.get("DEVSYNTH_RESOURCE_KUZU_AVAILABLE", "true").lower() == "false":
        return False
    try:  # pragma: no cover - simple import check
        import kuzu  # noqa: F401

        return True
    except ImportError:
        return False


class KuzuMemoryStore(MemoryStore):
    """Memory store using :class:`KuzuStore` with embedding support."""

    def __init__(
        self,
        persist_directory: str | None = None,
        use_provider_system: bool = True,
        provider_type: str | None = None,
        collection_name: str = "devsynth_artifacts",
    ) -> None:
        """Initialize a KuzuMemoryStore with the given parameters.

        Args:
            persist_directory: Directory to store data in. If ``None``, uses
                the default path.
            use_provider_system: Whether to use the provider system for
                embeddings.
            provider_type: Type of provider to use for embeddings.
            collection_name: Name of the collection to use for vectors.
        """
        self._temp_dir: str | None = None

        # Refresh settings to ensure environment overrides are respected
        current_settings = settings_module.get_settings()

        # Determine the base directory path with proper fallbacks
        base_directory = (
            persist_directory
            or getattr(current_settings, "kuzu_db_path", settings_module.kuzu_db_path)
            or os.path.join(os.getcwd(), ".devsynth", "kuzu_store")
        )

        # Normalize, expand and apply any test isolation redirections
        normalized_path = os.path.abspath(os.path.expanduser(base_directory))
        redirected_path = settings_module.ensure_path_exists(normalized_path)

        # Determine embedded mode from configuration.  Some older versions of
        # the settings module may not expose ``kuzu_embedded`` directly, so use
        # ``getattr`` with a sensible default.
        use_embedded = getattr(
            current_settings,
            "kuzu_embedded",
            getattr(
                settings_module,
                "kuzu_embedded",
                settings_module.DEFAULT_KUZU_EMBEDDED,
            ),
        )
        if not _is_kuzu_available():
            logger.info("Kuzu not available; using in-memory fallback store")
            use_embedded = False

        # Ensure both the database store and vector store are initialised on the
        # same usable path.  If initialisation fails (e.g. due to filesystem
        # permissions) fall back to a temporary directory and retry once.
        current_path = redirected_path
        temp_dir = None
        for _ in range(2):
            try:
                from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter

                self._store = KuzuStore(current_path, use_embedded=use_embedded)
                # ``KuzuStore`` may internally adjust the path; use its final value
                current_path = self._store.file_path
                self.vector = KuzuAdapter(current_path, collection_name)
                break
            except (ImportError, MemoryStoreError, OSError) as exc:
                logger.warning(
                    f"Initialization error for Kuzu memory at {current_path}: {exc}"
                )
                current_path = tempfile.mkdtemp(prefix="kuzu_store_")
                temp_dir = current_path
        else:
            raise MemoryStoreError("Failed to initialise Kuzu memory store")

        # Persist the final path used by both backends
        self.persist_directory = current_path
        if temp_dir:
            self._temp_dir = self.persist_directory

        self.use_provider_system = use_provider_system
        self.provider_type = provider_type

        # Set up embedder with better error handling
        try:
            if embedding_functions:
                self.embedder = embedding_functions.DefaultEmbeddingFunction()
            else:
                self.embedder = lambda x: [0.0] * 5
        except (AttributeError, TypeError) as e:
            logger.warning(f"Error initializing embedder: {e}. Using fallback.")
            self.embedder = lambda x: [0.0] * 5

        # Log the final state
        if hasattr(self._store, "_use_fallback") and self._store._use_fallback:
            logger.info("Kuzu unavailable; using in-memory fallback store")

        # Track active transaction contexts for coordinated commit/rollback
        # across the underlying item and vector stores.
        self._txn_contexts: dict[str, dict[str, Any]] = {}

    def _get_embedding(self, text: str):
        if self.use_provider_system:
            try:
                result = embed(text, provider_type=self.provider_type, fallback=True)
                if isinstance(result, list) and result:
                    first = result[0]
                    if first:
                        return first
                    logger.warning(
                        "Provider embedding returned empty result; falling back"
                    )
                else:
                    logger.warning(
                        "Provider embedding returned invalid data; falling back"
                    )
            except ProviderError:
                logger.warning("Provider embedding failed; falling back to default")
        return self.embedder(text)

    # ------------------------------------------------------------------
    # Transaction management

    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a coordinated transaction across item and vector stores."""

        tx_id = transaction_id or str(uuid.uuid4())
        if tx_id in self._txn_contexts:
            raise MemoryStoreError(f"Transaction {tx_id} already active")

        ctxs: dict[str, Any] = {}
        if hasattr(self._store, "transaction"):
            ctxs["store"] = self._store.transaction()
            ctxs["store"].__enter__()
        if hasattr(self.vector, "transaction"):
            ctxs["vector"] = self.vector.transaction(tx_id)
            ctxs["vector"].__enter__()
        self._txn_contexts[tx_id] = ctxs
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a previously started transaction."""

        ctxs = self._txn_contexts.pop(transaction_id, None)
        if ctxs is None:
            raise MemoryStoreError(
                f"Commit requested for unknown transaction {transaction_id}"
            )
        errors = []
        for ctx in ctxs.values():
            try:
                ctx.__exit__(None, None, None)
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(exc)
        if errors:
            raise MemoryStoreError(
                f"Error committing transaction {transaction_id}: {errors[0]}"
            )
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a previously started transaction."""

        ctxs = self._txn_contexts.pop(transaction_id, None)
        if ctxs is None:
            raise MemoryStoreError(
                f"Rollback requested for unknown transaction {transaction_id}"
            )
        errors = []
        exc = ValueError("rollback")
        for ctx in ctxs.values():
            try:
                ctx.__exit__(ValueError, exc, exc.__traceback__)
            except Exception as err:  # pragma: no cover - defensive
                errors.append(err)
        if errors:
            raise MemoryStoreError(
                f"Error rolling back transaction {transaction_id}: {errors[0]}"
            )
        return True

    @contextmanager
    def transaction(self, transaction_id: str | None = None):
        """Context manager for transactional operations."""

        tx_id = self.begin_transaction(transaction_id)
        try:
            yield tx_id
        except Exception:
            self.rollback_transaction(tx_id)
            raise
        else:
            self.commit_transaction(tx_id)

    def store(self, item: MemoryItem) -> str:
        """Store a memory item and its vector representation.

        This method ensures that both the memory item and its vector are stored
        consistently, using transaction support when available.

        Args:
            item: The memory item to store

        Returns:
            The ID of the stored item

        Raises:
            MemoryStoreError: If there's an error storing the item or vector
        """
        try:
            # Get embedding with better error handling
            embedding = self._get_embedding(str(item.content))
            if not embedding:
                logger.warning(
                    f"Empty embedding generated for item {item.id}. Using fallback."
                )
                embedding = [0.0] * 5

            # Create vector object
            vector = MemoryVector(
                id=item.id,
                content=item.content,
                embedding=embedding,
                metadata=item.metadata,
            )

            # Use transaction if available
            if hasattr(self._store, "transaction"):
                with self._store.transaction():
                    # Store both items, starting with the vector
                    vector_id = self.vector.store_vector(vector)
                    item_id = self._store.store(item)

                    # Verify consistency
                    if vector_id != item_id:
                        logger.warning(
                            f"Vector ID {vector_id} doesn't match item ID {item_id}. "
                            f"This might cause retrieval issues."
                        )
                    return item_id
            else:
                # No transaction support, store sequentially
                vector_id = self.vector.store_vector(vector)
                item_id = self._store.store(item)
                return item_id

        except (MemoryStoreError, OSError) as e:
            logger.error(f"Error storing item {item.id}: {e}")
            # Try to clean up any partial storage
            try:
                self.vector.delete_vector(item.id)
            except (MemoryStoreError, OSError) as cleanup_error:
                logger.warning(
                    "Failed to delete vector for %s during rollback: %s",
                    item.id,
                    cleanup_error,
                )
            try:
                self._store.delete(item.id)
            except (MemoryStoreError, OSError) as cleanup_error:
                logger.warning(
                    "Failed to delete item %s during rollback cleanup: %s",
                    item.id,
                    cleanup_error,
                )
            raise MemoryStoreError(f"Failed to store item {item.id}: {e}") from e

    def retrieve(self, item_id: str) -> MemoryItem | None:
        return self._store.retrieve(item_id)

    def search(self, query: dict[str, Any]):
        query_text = query.get("query")
        top_k = query.get("top_k", 5)
        embedding = self._get_embedding(str(query_text))
        vectors = self.vector.similarity_search(embedding, top_k=top_k)
        results = []
        for v in vectors:
            item = self.retrieve(v.id)
            if item:
                results.append(item)
        return results

    def delete(self, item_id: str) -> bool:
        """Delete a memory item and its vector representation.

        This method ensures that both the memory item and its vector are deleted
        consistently, using transaction support when available.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False otherwise

        Raises:
            MemoryStoreError: If there's an error deleting the item or vector
        """
        try:
            # Use transaction if available
            if hasattr(self._store, "transaction"):
                with self._store.transaction():
                    # Delete both items
                    vector_deleted = self.vector.delete_vector(item_id)
                    item_deleted = self._store.delete(item_id)

                    # Log inconsistency but don't fail
                    if vector_deleted != item_deleted:
                        logger.warning(
                            "Inconsistent delete results for item %s: "
                            "vector_deleted=%s, item_deleted=%s",
                            item_id,
                            vector_deleted,
                            item_deleted,
                        )

                    # Return True if either was deleted
                    return vector_deleted or item_deleted
            else:
                # No transaction support, delete sequentially
                # Delete vector first to avoid orphaned vectors
                vector_deleted = self.vector.delete_vector(item_id)
                item_deleted = self._store.delete(item_id)

                # Return True if either was deleted
                return vector_deleted or item_deleted

        except (MemoryStoreError, OSError) as e:
            logger.error(f"Error deleting item {item_id}: {e}")
            # Don't raise here to maintain backward compatibility
            # Just log and return False
            return False

    # ------------------------------------------------------------------
    @classmethod
    def create_ephemeral(
        cls,
        use_provider_system: bool = True,
        provider_type: str | None = None,
        collection_name: str = "devsynth_artifacts",
    ) -> KuzuMemoryStore:
        """Create an ephemeral ``KuzuMemoryStore`` for tests.

        The settings are reloaded so that environment-variable overrides are
        respected during store initialization.
        """
        # Ensure fresh settings in case tests modified environment variables
        settings_module.get_settings(reload=True)
        temp_dir = tempfile.mkdtemp(prefix="kuzu_")
        store = cls(
            persist_directory=temp_dir,
            use_provider_system=use_provider_system,
            provider_type=provider_type,
            collection_name=collection_name,
        )
        # Track the actual directory used after any path redirection
        store._temp_dir = store.persist_directory
        return store

    def cleanup(self) -> None:
        """Remove any temporary directory created by :meth:`create_ephemeral`.

        This method ensures that all temporary files and directories are properly
        cleaned up, including those created by KuzuStore and KuzuAdapter.
        """
        # First, allow the underlying store to release resources
        try:
            if hasattr(self, "_store") and hasattr(self._store, "close"):
                self._store.close()
        except (MemoryStoreError, OSError) as e:
            logger.warning(f"Error closing Kuzu store: {e}")

        # Clean up vector store files
        try:
            vector_data_file = getattr(self.vector, "_data_file", None)
            if vector_data_file and os.path.exists(vector_data_file):
                try:
                    os.remove(vector_data_file)
                    logger.debug(f"Removed vector data file: {vector_data_file}")
                except OSError as e:
                    logger.warning(f"Failed to remove vector data file: {e}")

            # Also try to remove any temporary files
            vector_temp_file = f"{vector_data_file}.tmp" if vector_data_file else None
            if vector_temp_file and os.path.exists(vector_temp_file):
                try:
                    os.remove(vector_temp_file)
                    logger.debug(f"Removed vector temp file: {vector_temp_file}")
                except OSError as exc:
                    logger.warning(
                        "Failed to remove vector temp file %s: %s",
                        vector_temp_file,
                        exc,
                    )
        except OSError as e:
            logger.warning(f"Error during vector store cleanup: {e}")

        # Finally, remove the temporary directory
        temp_dir = getattr(self, "_temp_dir", None)
        if temp_dir and os.path.exists(temp_dir):
            try:
                # Use a short delay to ensure files are not locked
                time.sleep(0.1)
                shutil.rmtree(temp_dir)
                logger.debug(f"Removed temporary directory: {temp_dir}")
            except OSError as exc:
                logger.warning(f"Failed to clean up temporary Kuzu directory: {exc}")
                # Try to remove individual files as a fallback
                try:
                    for root, dirs, files in os.walk(temp_dir, topdown=False):
                        for file in files:
                            try:
                                os.remove(os.path.join(root, file))
                            except OSError as remove_error:
                                logger.debug(
                                    "Unable to remove temporary file %s: %s",
                                    os.path.join(root, file),
                                    remove_error,
                                )
                        for dir in dirs:
                            try:
                                os.rmdir(os.path.join(root, dir))
                            except OSError as remove_error:
                                logger.debug(
                                    "Unable to remove temporary directory %s: %s",
                                    os.path.join(root, dir),
                                    remove_error,
                                )
                    # Try to remove the root directory again
                    try:
                        os.rmdir(temp_dir)
                    except OSError as remove_error:
                        logger.debug(
                            "Unable to remove temporary root directory %s: %s",
                            temp_dir,
                            remove_error,
                        )
                except OSError as cleanup_error:
                    logger.warning(
                        "Error during fallback cleanup of temporary directory %s: %s",
                        temp_dir,
                        cleanup_error,
                    )

        if temp_dir:
            self._temp_dir = None

    def get_all_items(self) -> list[MemoryItem]:
        """Return all stored items."""

        return self._store.get_all_items()

    # ------------------------------------------------------------------
    def store_vector(self, vector: MemoryVector) -> str:
        """Store a vector using the underlying ``KuzuAdapter``."""

        return self.vector.store_vector(vector)

    def retrieve_vector(self, vector_id: str) -> MemoryVector | None:
        """Retrieve a stored vector by ID."""

        return self.vector.retrieve_vector(vector_id)

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector by ID."""

        return self.vector.delete_vector(vector_id)

    def get_all_vectors(self) -> list[MemoryVector]:
        """Return all stored vectors."""

        return self.vector.get_all_vectors()
