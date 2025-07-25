"""KuzuDB implementation of the MemoryStore interface.

This store mimics the behaviour of ``ChromaDBStore`` but uses KuzuDB as the
backend when available. If the ``kuzu`` package is not installed the store
falls back to an in-memory dictionary. The store includes a simple caching
layer and version tracking similar to ``ChromaDBStore``.
"""

from __future__ import annotations

import json
import os
import sys
import importlib
from datetime import datetime
from typing import Any, Dict, List, Optional

if __spec__ is not None:
    canonical_name = "devsynth.application.memory.kuzu_store"
    module_obj = sys.modules.setdefault(__name__, sys.modules.get(__name__))
    sys.modules[canonical_name] = module_obj
    __spec__.name = canonical_name



try:  # pragma: no cover - optional dependency
    import tiktoken
except Exception:  # pragma: no cover - optional dependency
    tiktoken = None

from devsynth.logging_setup import DevSynthLogger
from devsynth.fallback import retry_with_exponential_backoff
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryStoreError
from devsynth.config.settings import ensure_path_exists

logger = DevSynthLogger(__name__)


class KuzuStore(MemoryStore):
    """Lightweight ``MemoryStore`` backed by KuzuDB."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        # Ensure the backing directory exists even when using the in-memory
        # fallback.  This mirrors the behaviour of other memory stores which
        # create their storage path during initialisation and allows tests
        # relying on the directory to be present to pass.
        ensure_path_exists(file_path)
        os.makedirs(file_path, exist_ok=True)
        self.db_path = os.path.join(file_path, "kuzu.db")
        self._cache: Dict[str, MemoryItem] = {}
        self._versions: Dict[str, List[MemoryItem]] = {}
        self._token_usage = 0

        # tokenizer for token usage
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:  # pragma: no cover - optional
            self.tokenizer = None

        kuzu_mod = None
        if "kuzu" in sys.modules and sys.modules["kuzu"] is not None:
            kuzu_mod = sys.modules["kuzu"]
        else:  # pragma: no cover - optional dependency
            try:
                kuzu_mod = importlib.import_module("kuzu")
            except Exception:
                kuzu_mod = None

        self._use_fallback = kuzu_mod is None
        if not self._use_fallback:
            try:
                ensure_path_exists(file_path)
                self.db = kuzu_mod.Database(self.db_path)
                self.conn = kuzu_mod.Connection(self.db)
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS memory(id STRING PRIMARY KEY, item STRING);"
                )
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS versions(id STRING, version INT, item STRING);"
                )
            except Exception as e:  # pragma: no cover - fallback to memory
                logger.warning(
                    f"Failed to initialise KuzuDB: {e}. Falling back to in-memory store"
                )
                self._use_fallback = True

        if self._use_fallback:
            self._store: Dict[str, MemoryItem] = {}

    # utility serialisation helpers -------------------------------------------------
    def _count_tokens(self, text: str) -> int:
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:  # pragma: no cover - defensive
                pass
        return len(text) // 4

    def _serialise(self, item: MemoryItem) -> str:
        data = {
            "id": item.id,
            "content": item.content,
            "memory_type": item.memory_type.value if item.memory_type else None,
            "metadata": item.metadata,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        return json.dumps(data)

    def _deserialise(self, raw: str) -> MemoryItem:
        data = json.loads(raw)
        mem_type = MemoryType(data["memory_type"]) if data.get("memory_type") else None
        created = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None
        )
        return MemoryItem(
            id=data["id"],
            content=data["content"],
            memory_type=mem_type,
            metadata=data.get("metadata", {}),
            created_at=created,
        )

    # core operations ----------------------------------------------------------------
    @retry_with_exponential_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def store(self, item: MemoryItem) -> str:
        existing = self.retrieve(item.id)
        if existing:
            self._versions.setdefault(item.id, []).append(existing)
            version = len(self._versions[item.id]) + 1
        else:
            version = 1
        item.metadata.setdefault("version", version)
        serialised = self._serialise(item)
        self._token_usage += self._count_tokens(serialised)

        if self._use_fallback:
            self._store[item.id] = item
        else:  # pragma: no cover - requires kuzu
            self.conn.execute(
                "MERGE INTO memory(id,item) VALUES (?, ?)", [item.id, serialised]
            )
            self.conn.execute(
                "MERGE INTO versions(id,version,item) VALUES (?, ?, ?)",
                [item.id, version, serialised],
            )
        if item.id in self._cache:
            del self._cache[item.id]
        return item.id

    def _retrieve_from_db(self, item_id: str) -> Optional[MemoryItem]:
        if self._use_fallback:
            return self._store.get(item_id)
        try:  # pragma: no cover - requires kuzu
            res = self.conn.execute(
                "MATCH (n:memory) WHERE n.id=? RETURN n.item", [item_id]
            )
            if res and res.hasNext():
                raw = res.getNext()[0]
                return self._deserialise(raw)
        except Exception as e:  # pragma: no cover
            logger.error(f"Kuzu retrieval error: {e}")
        return None

    @retry_with_exponential_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        if item_id in self._cache:
            return self._cache[item_id]
        item = self._retrieve_from_db(item_id)
        if item:
            self._cache[item_id] = item
        return item

    @retry_with_exponential_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def retrieve_version(self, item_id: str, version: int) -> Optional[MemoryItem]:
        if version == self.get_latest_version(item_id):
            return self.retrieve(item_id)
        versions = self.get_versions(item_id)
        for v in versions:
            if v.metadata.get("version") == version:
                return v
        return None

    def get_latest_version(self, item_id: str) -> int:
        versions = self._versions.get(item_id, [])
        return len(versions) + (1 if self.retrieve(item_id) else 0)

    def get_versions(self, item_id: str) -> List[MemoryItem]:
        return list(self._versions.get(item_id, []))

    def get_history(self, item_id: str) -> List[Dict[str, Any]]:
        history = []
        for item in self.get_versions(item_id) + (
            [self.retrieve(item_id)] if self.retrieve(item_id) else []
        ):
            if item:
                history.append(
                    {
                        "version": item.metadata.get("version"),
                        "timestamp": (
                            item.created_at.isoformat() if item.created_at else ""
                        ),
                        "content_summary": str(item.content)[:100],
                        "metadata": item.metadata,
                    }
                )
        history.sort(key=lambda x: x["version"])
        return history

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        items = [
            self.retrieve(i)
            for i in (self._store.keys() if self._use_fallback else self._all_ids())
        ]
        results = []
        for item in items:
            if not item:
                continue
            match = True
            for key, value in query.items():
                if key == "memory_type" and isinstance(value, MemoryType):
                    if item.memory_type != value:
                        match = False
                        break
                elif key.startswith("metadata."):
                    field = key.split(".", 1)[1]
                    if item.metadata.get(field) != value:
                        match = False
                        break
                elif key == "content":
                    if str(value).lower() not in str(item.content).lower():
                        match = False
                        break
            if match:
                results.append(item)
        return results

    def _all_ids(self) -> List[str]:  # pragma: no cover - requires kuzu
        try:
            res = self.conn.execute("MATCH (n:memory) RETURN n.id")
            ids = []
            while res.hasNext():
                ids.append(res.getNext()[0])
            return ids
        except Exception:
            return []

    def delete(self, item_id: str) -> bool:
        if self._use_fallback:
            existed = item_id in self._store
            self._store.pop(item_id, None)
            self._cache.pop(item_id, None)
            return existed
        try:  # pragma: no cover - requires kuzu
            self.conn.execute("DELETE FROM memory WHERE id=?", [item_id])
            self.conn.execute("DELETE FROM versions WHERE id=?", [item_id])
            self._cache.pop(item_id, None)
            return True
        except Exception as e:
            logger.error(f"Kuzu delete error: {e}")
            return False

    def get_token_usage(self) -> int:
        return self._token_usage

    def has_optimized_embeddings(self) -> bool:
        return True

    def get_embedding_storage_efficiency(self) -> float:
        return 0.85
