"""Adapter for ``KuzuStore`` integrating provider embeddings."""

from __future__ import annotations

import os
import tempfile
import shutil
from typing import Any, Dict, Optional, List

from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryVector
from devsynth.logging_setup import DevSynthLogger
from devsynth.adapters.provider_system import embed, ProviderError
from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.config import settings as settings_module

try:  # pragma: no cover - optional dependency
    from chromadb.utils import embedding_functions
except Exception:  # pragma: no cover - optional dependency
    embedding_functions = None

logger = DevSynthLogger(__name__)


class KuzuMemoryStore(MemoryStore):
    """Memory store using :class:`KuzuStore` with embedding support."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        use_provider_system: bool = True,
        provider_type: Optional[str] = None,
        collection_name: str = "devsynth_artifacts",
    ) -> None:
        self._temp_dir: Optional[str] = None
        self.persist_directory = (
            persist_directory
            or settings_module.kuzu_db_path
            or os.path.join(os.getcwd(), ".devsynth", "kuzu_store")
        )
        # ``ensure_path_exists`` may redirect the path when running under the
        # test isolation fixtures.  Capture the returned value so both the
        # ``KuzuStore`` and ``KuzuAdapter`` use the same final directory.
        self.persist_directory = settings_module.ensure_path_exists(
            self.persist_directory
        )
        
        # Explicitly determine whether to use embedded mode
        use_embedded = getattr(settings_module, "KUZU_EMBEDDED", 
                              getattr(settings_module._settings, "kuzu_embedded", True))
        if isinstance(use_embedded, str):
            use_embedded = use_embedded.lower() in {"1", "true", "yes"}
        
        # Create the directory to ensure it exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        try:
            self._store = KuzuStore(self.persist_directory, use_embedded=use_embedded)
            self.vector = KuzuAdapter(self.persist_directory, collection_name)
        except Exception as e:
            logger.warning(f"Error initializing Kuzu store: {e}. Using fallback.")
            # Ensure fallback is used
            self._store = KuzuStore(self.persist_directory, use_embedded=False)
            self.vector = KuzuAdapter(self.persist_directory, collection_name)
            
        self.use_provider_system = use_provider_system
        self.provider_type = provider_type
        
        # Set up embedder with better error handling
        try:
            if embedding_functions:
                self.embedder = embedding_functions.DefaultEmbeddingFunction()
            else:
                self.embedder = lambda x: [0.0] * 5
        except Exception as e:
            logger.warning(f"Error initializing embedder: {e}. Using fallback.")
            self.embedder = lambda x: [0.0] * 5

        if self._store._use_fallback:
            logger.info("Kuzu unavailable; using in-memory fallback store")

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

    def store(self, item: MemoryItem) -> str:
        embedding = self._get_embedding(str(item.content))
        self.vector.store_vector(
            MemoryVector(
                id=item.id,
                content=item.content,
                embedding=embedding,
                metadata=item.metadata,
            )
        )
        return self._store.store(item)

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        return self._store.retrieve(item_id)

    def search(self, query: Dict[str, Any]):
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
        self.vector.delete_vector(item_id)
        return self._store.delete(item_id)

    # ------------------------------------------------------------------
    @classmethod
    def create_ephemeral(
        cls,
        use_provider_system: bool = True,
        provider_type: Optional[str] = None,
        collection_name: str = "devsynth_artifacts",
    ) -> "KuzuMemoryStore":
        """Create an ephemeral ``KuzuMemoryStore`` for tests."""
        temp_dir = tempfile.mkdtemp(prefix="kuzu_")
        store = cls(
            persist_directory=temp_dir,
            use_provider_system=use_provider_system,
            provider_type=provider_type,
            collection_name=collection_name,
        )
        store._temp_dir = temp_dir
        return store

    def cleanup(self) -> None:
        """Remove any temporary directory created by :meth:`create_ephemeral`."""
        temp_dir = getattr(self, "_temp_dir", None)
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to clean up temporary Kuzu directory: %s", exc)
        if temp_dir:
            self._temp_dir = None

    def get_all_items(self) -> List[MemoryItem]:
        """Return all stored items."""

        return self._store.get_all_items()

    # ------------------------------------------------------------------
    def store_vector(self, vector: MemoryVector) -> str:
        """Store a vector using the underlying ``KuzuAdapter``."""

        return self.vector.store_vector(vector)

    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:
        """Retrieve a stored vector by ID."""

        return self.vector.retrieve_vector(vector_id)

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector by ID."""

        return self.vector.delete_vector(vector_id)

    def get_all_vectors(self) -> List[MemoryVector]:
        """Return all stored vectors."""

        return self.vector.get_all_vectors()
