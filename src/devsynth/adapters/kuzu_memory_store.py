"""Adapter for ``KuzuStore`` integrating provider embeddings."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryVector
from devsynth.logging_setup import DevSynthLogger
from devsynth.adapters.provider_system import embed, ProviderError
from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.config.settings import ensure_path_exists

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
        self.persist_directory = persist_directory or os.path.join(
            os.getcwd(), ".devsynth", "kuzu_store"
        )
        ensure_path_exists(self.persist_directory)
        self._store = KuzuStore(self.persist_directory)
        self.vector = KuzuAdapter(self.persist_directory, collection_name)
        self.use_provider_system = use_provider_system
        self.provider_type = provider_type
        if embedding_functions:
            self.embedder = embedding_functions.DefaultEmbeddingFunction()
        else:
            self.embedder = lambda x: [0.0] * 5

    def _get_embedding(self, text: str):
        if self.use_provider_system:
            try:
                result = embed(text, provider_type=self.provider_type, fallback=True)
                if isinstance(result, list):
                    return result[0]
            except ProviderError:
                logger.warning("Provider embedding failed; falling back to default")
        return self.embedder(text)

    def store(self, item: MemoryItem) -> str:
        embedding = self._get_embedding(str(item.content))
        self.vector.store_vector(
            MemoryVector(id=item.id, content=item.content, embedding=embedding, metadata=item.metadata)
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
