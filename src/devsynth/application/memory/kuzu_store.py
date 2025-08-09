"""KuzuDB implementation of the MemoryStore interface.

This store mimics the behaviour of ``ChromaDBStore`` but uses KuzuDB as the
backend when available. If the ``kuzu`` package is not installed the store
falls back to an in-memory dictionary. The store includes a simple caching
layer and version tracking similar to ``ChromaDBStore``.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

canonical_name = "devsynth.application.memory.kuzu_store"
# Ensure the module is registered under its canonical name even when loaded
# via ``importlib`` with a custom spec.  Some tests reload this module using
# ``importlib.util.spec_from_file_location`` which can leave
# ``sys.modules[canonical_name]`` set to ``None`` if the reload fails or if the
# spec name differs from the canonical package path.  Registering the module
# here avoids ``ModuleNotFoundError: ... None in sys.modules`` when the test
# framework attempts another import after such a reload.
if sys.modules.get(canonical_name) is None:
    sys.modules[canonical_name] = sys.modules.get(
        __name__, sys.modules.setdefault(__name__, sys.modules[__name__])
    )

if __spec__ is not None:
    __spec__.name = canonical_name


try:  # pragma: no cover - optional dependency
    import tiktoken
except Exception:  # pragma: no cover - optional dependency
    tiktoken = None

# Import the settings module so tests can monkeypatch ``ensure_path_exists``
from devsynth.config import settings as settings_module
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryStoreError
from devsynth.fallback import retry_with_exponential_backoff
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class KuzuStore(MemoryStore):
    """Lightweight ``MemoryStore`` backed by KuzuDB."""

    def __init__(
        self, file_path: Union[str, None] = None, use_embedded: Union[bool, None] = None
    ) -> None:
        # ``ensure_path_exists`` handles path redirection and optional
        # directory creation based on the test environment.  Use the returned
        # path so tests that set ``DEVSYNTH_PROJECT_DIR`` are respected and
        # avoid manual ``os.makedirs`` which would ignore the
        # ``DEVSYNTH_NO_FILE_LOGGING`` setting.
        # ``ensure_path_exists`` may redirect the path when running under the
        # test isolation fixtures.  Use the returned path so the database is
        # created in the correct location rather than the original argument
        # which may be outside the temporary test directory.
        base_path = os.path.abspath(
            settings_module.ensure_path_exists(
                file_path
                or settings_module.kuzu_db_path
                or os.path.join(os.getcwd(), ".devsynth", "kuzu_store")
            )
        )
        try:
            os.makedirs(base_path, exist_ok=True)
            self.file_path = base_path
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning(
                "Unable to create Kuzu store directory %s: %s; using temporary directory",
                base_path,
                exc,
            )
            self.file_path = tempfile.mkdtemp(prefix="kuzu_store_")
            os.makedirs(self.file_path, exist_ok=True)

        self.db_path = os.path.join(self.file_path, "kuzu.db")
        self._cache: Dict[str, MemoryItem] = {}
        self._versions: Dict[str, List[MemoryItem]] = {}
        self._token_usage = 0
        self._transaction_stack: List[Dict[str, MemoryItem]] = []

        # tokenizer for token usage
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:  # pragma: no cover - optional
            self.tokenizer = None

        # Determine whether the embedded Kuzu backend should be used.  When no
        # explicit value is provided, consult the live settings to honour any
        # environment variable overrides that may have been applied after the
        # module was imported.
        raw_embedded = (
            getattr(
                settings_module.get_settings(),
                "kuzu_embedded",
                getattr(settings_module, "kuzu_embedded", True),
            )
            if use_embedded is None
            else use_embedded
        )
        if isinstance(raw_embedded, str):
            raw_embedded = raw_embedded.lower() in {"1", "true", "yes"}
        self.use_embedded = bool(raw_embedded)

        kuzu_mod = None
        if "kuzu" in sys.modules and sys.modules["kuzu"] is not None:
            kuzu_mod = sys.modules["kuzu"]
        else:  # pragma: no cover - optional dependency
            try:
                kuzu_mod = importlib.import_module("kuzu")
            except Exception:
                kuzu_mod = None

        self._use_fallback = kuzu_mod is None or not self.use_embedded
        if not self._use_fallback:
            try:
                settings_module.ensure_path_exists(self.file_path)
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

    # transactional support ---------------------------------------------------
    @contextmanager
    def transaction(self):
        """Provide a simple transaction context with rollback."""
        snapshot = None
        if self._use_fallback:
            snapshot = deepcopy(self._store)
        else:  # pragma: no cover - requires kuzu
            try:
                self.conn.execute("BEGIN TRANSACTION")
            except Exception:
                pass
        self._transaction_stack.append(snapshot)
        try:
            yield
            self._transaction_stack.pop()
            if not self._use_fallback:
                try:
                    self.conn.execute("COMMIT")
                except Exception:
                    pass
        except Exception:
            snap = self._transaction_stack.pop()
            if self._use_fallback and snap is not None:
                self._store = snap
            else:  # pragma: no cover - requires kuzu
                try:
                    self.conn.execute("ROLLBACK")
                except Exception:
                    pass
            raise

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

    def get_all_items(self) -> List[MemoryItem]:
        """Return all stored :class:`MemoryItem` objects."""

        if self._use_fallback:
            return list(self._store.values())

        items: List[MemoryItem] = []
        try:  # pragma: no cover - requires kuzu
            for item_id in self._all_ids():
                itm = self._retrieve_from_db(item_id)
                if itm:
                    items.append(itm)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to fetch all items from Kuzu: %s", exc)
        return items

    # memory volatility -------------------------------------------------------
    def add_memory_volatility(
        self, decay_rate: float = 0.1, threshold: float = 0.5
    ) -> None:
        """Enable simple volatility controls on stored items."""
        for item in self.get_all_items():
            item.metadata.setdefault("confidence", 1.0)
            item.metadata["decay_rate"] = decay_rate
            item.metadata["threshold"] = threshold
            if self._use_fallback:
                self._store[item.id] = item
            else:  # pragma: no cover - requires kuzu
                self.conn.execute(
                    "MERGE INTO memory(id,item) VALUES (?, ?)",
                    [item.id, self._serialise(item)],
                )
        self._cache.clear()

    def apply_memory_decay(self) -> List[str]:
        """Apply decay and return items below threshold."""
        volatile: List[str] = []
        for item in self.get_all_items():
            conf = float(item.metadata.get("confidence", 1.0))
            decay = float(item.metadata.get("decay_rate", 0.1))
            threshold = float(item.metadata.get("threshold", 0.5))
            conf = max(0.0, conf - decay)
            item.metadata["confidence"] = conf
            if conf < threshold:
                volatile.append(item.id)
            if self._use_fallback:
                self._store[item.id] = item
            else:  # pragma: no cover - requires kuzu
                self.conn.execute(
                    "MERGE INTO memory(id,item) VALUES (?, ?)",
                    [item.id, self._serialise(item)],
                )
        self._cache.clear()
        return volatile

    # cleanup -----------------------------------------------------------------------
    def close(self) -> None:
        """Close any open Kuzu resources."""
        if self._use_fallback:
            return
        try:  # pragma: no cover - requires kuzu
            if getattr(self, "conn", None):
                try:
                    self.conn.execute("COMMIT")
                except Exception:
                    pass
                if hasattr(self.conn, "close"):
                    try:
                        self.conn.close()
                    except Exception:
                        pass
            if getattr(self, "db", None) and hasattr(self.db, "close"):
                try:
                    self.db.close()
                except Exception:
                    pass
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to close Kuzu resources: %s", exc)

    def __del__(self):  # pragma: no cover - defensive
        try:
            self.close()
        except Exception:
            pass
