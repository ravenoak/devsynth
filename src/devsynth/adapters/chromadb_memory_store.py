import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import Any, Dict, List, Optional, Union
from devsynth.ports.memory_store import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from datetime import datetime
from devsynth.adapters.provider_system import get_provider, embed

class ChromaDBMemoryStore(MemoryStore):
    """
    ChromaDB-backed implementation of the MemoryStore interface.
    Stores and retrieves artifacts with semantic search using embeddings.

    Integrates with the provider system to leverage either OpenAI or LM Studio
    for embeddings, with automatic fallback if a provider fails.
    """
    def __init__(self,
                persist_directory: str = ".devsynth/chromadb_store",
                use_provider_system: bool = True,
                provider_type: Optional[str] = None):
        """
        Initialize the ChromaDB memory store.

        Args:
            persist_directory: Directory to persist ChromaDB data
            use_provider_system: Whether to use the provider system for embeddings
            provider_type: Optional specific provider to use (if use_provider_system is True)
        """
        self.client = chromadb.Client(Settings(persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection("devsynth_artifacts")

        # Use provider system for embeddings if specified, otherwise fallback to default
        self.use_provider_system = use_provider_system
        self.provider_type = provider_type

        if not use_provider_system:
            # Fallback to default ChromaDB embedding function
            self.embedder = embedding_functions.DefaultEmbeddingFunction()

    def _get_embedding(self, text: Union[str, List[str]]) -> List[float]:
        """
        Get embedding for text using the provider system or default embedder.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.use_provider_system:
            try:
                # Use provider system with fallback
                embedding_results = embed(text, provider_type=self.provider_type, fallback=True)
                # Provider system returns list of embeddings, take first one for single text
                if isinstance(text, str):
                    return embedding_results[0]
                return embedding_results
            except Exception as e:
                # Log error and fall back to default embedder if provider system fails
                from devsynth.logging_setup import DevSynthLogger
                logger = DevSynthLogger(__name__)
                logger.warning(f"Provider system embedding failed: {e}. Falling back to default embedder.")

                # Initialize default embedder if needed
                if not hasattr(self, 'embedder'):
                    self.embedder = embedding_functions.DefaultEmbeddingFunction()

                return self.embedder(text)
        else:
            # Use default embedder
            return self.embedder(text)

    def store(self, item: MemoryItem) -> str:
        content = item.content
        metadata = dict(item.metadata or {})
        metadata["memory_type"] = item.memory_type.value if hasattr(item.memory_type, 'value') else str(item.memory_type)
        metadata["created_at"] = item.created_at.isoformat() if item.created_at else datetime.now().isoformat()

        # Use provider system for embeddings
        embedding = self._get_embedding(content)

        item_id = item.id or str(hash(content))
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[item_id],
            embeddings=[embedding],
        )
        return item_id

    def retrieve(self, item_id: str) -> MemoryItem:
        results = self.collection.get(ids=[item_id])
        if not results["documents"]:
            raise KeyError(f"Item {item_id} not found.")
        doc = results["documents"][0]
        meta = results["metadatas"][0]
        return MemoryItem(
            id=item_id,
            content=doc,
            memory_type=MemoryType(meta.get("memory_type", "WORKING")),
            metadata=meta,
            created_at=datetime.fromisoformat(meta["created_at"]) if "created_at" in meta else datetime.now(),
        )

    def search(self, query: dict) -> list:
        # Accepts a dict with 'query' and optional 'top_k'
        query_text = query.get("query")
        top_k = query.get("top_k", 5)

        # Use provider system for embeddings
        embedding = self._get_embedding(query_text)

        results = self.collection.query(query_embeddings=[embedding], n_results=top_k)
        items = []
        for doc, meta, id_ in zip(results["documents"][0], results["metadatas"][0], results["ids"][0]):
            items.append(MemoryItem(
                id=id_,
                content=doc,
                memory_type=MemoryType(meta.get("memory_type", "WORKING")),
                metadata=meta,
                created_at=datetime.fromisoformat(meta["created_at"]) if "created_at" in meta else datetime.now(),
            ))
        return items

    def delete(self, item_id: str) -> bool:
        self.collection.delete(ids=[item_id])
        return True
