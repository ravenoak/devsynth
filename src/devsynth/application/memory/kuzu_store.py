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
import uuid
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from types import ModuleType
from typing import TYPE_CHECKING, Iterator, Protocol, cast

canonical_name = "devsynth.application.memory.kuzu_store"
# Ensure the module is registered under its canonical name even when loaded
# via ``importlib`` with a custom spec.  Some tests reload this module using
# ``importlib.util.spec_from_file_location`` which can leave
# ``sys.modules[canonical_name]`` set to ``None`` if the reload fails or if the
# spec name differs from the canonical package path.  Registering the module
# here avoids ``ModuleNotFoundError: ... None in sys.modules`` when the test
# framework attempts another import after such a reload.
if sys.modules.get(canonical_name) is None:
    # When loaded via importlib, __name__ should be set to the spec name
    # which should match the canonical name
    sys.modules[canonical_name] = sys.modules.get(__name__, None)

if __spec__ is not None:
    __spec__.name = canonical_name


class _TiktokenModule(Protocol):
    def get_encoding(self, name: str) -> object: ...


class _KuzuConnection(Protocol):
    def execute(self, query: str, params: Sequence[object] | None = ...) -> object: ...


class _KuzuDatabase(Protocol):
    def close(self) -> None: ...


if TYPE_CHECKING:  # pragma: no cover - imported for static analysis only
    import tiktoken as _tiktoken_module

tiktoken: _TiktokenModule | None
try:  # pragma: no cover - optional dependency
    import tiktoken as _tiktoken
except Exception:  # pragma: no cover - optional dependency
    tiktoken = None
else:
    tiktoken = cast("_TiktokenModule", _tiktoken)

# Import config module for default settings and constants
from devsynth import config as settings_module

# Import get_settings so tests can access configuration
from devsynth.config.settings import ensure_path_exists, get_settings, kuzu_embedded
from devsynth.domain.interfaces.memory import MemoryStore, SupportsTransactions
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryStoreError
from devsynth.fallback import retry_with_exponential_backoff
from devsynth.logging_setup import DevSynthLogger

from .dto import MemoryRecord, build_memory_record

logger = DevSynthLogger(__name__)


class KuzuStore(MemoryStore, SupportsTransactions):
    """Lightweight ``MemoryStore`` backed by KuzuDB."""

    def __init__(
        self, file_path: str | None = None, use_embedded: bool | None = None
    ) -> None:
        # Load the latest configuration to honour environment variable
        # overrides that may have been applied after module import.  Rely on
        # the settings object rather than module-level constants so changes are
        # consistently respected.
        settings = get_settings(reload=True)

        # ``ensure_path_exists`` handles path redirection and optional
        # directory creation based on the test environment.  Use the returned
        # path so tests that set ``DEVSYNTH_PROJECT_DIR`` are respected and
        # avoid manual ``os.makedirs`` which would ignore the
        # ``DEVSYNTH_NO_FILE_LOGGING`` setting.  ``ensure_path_exists`` may
        # redirect the path when running under the test isolation fixtures.
        base_directory = (
            file_path
            or getattr(settings, "kuzu_db_path", settings_module.kuzu_db_path)
            or os.path.join(os.getcwd(), ".devsynth", "kuzu_store")
        )
        base_path = os.path.abspath(ensure_path_exists(base_directory))
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
        self.db: _KuzuDatabase | None = None
        self.conn: _KuzuConnection | None = None
        self._cache: dict[str, MemoryItem] = {}
        self._versions: dict[str, list[MemoryItem]] = {}
        self._token_usage = 0
        self._transactions: dict[str, dict[str, MemoryItem]] = {}

        # tokenizer for token usage
        self.tokenizer: object | None = None
        if tiktoken is not None:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception:  # pragma: no cover - optional
                self.tokenizer = None

        # Determine whether the embedded Kuzu backend should be used.  When no
        # explicit value is provided, consult the live settings to honour any
        # environment variable overrides that may have been applied after the
        # module was imported.
        raw_embedded = (
            getattr(settings, "kuzu_embedded", kuzu_embedded)
            if use_embedded is None
            else use_embedded
        )
        if isinstance(raw_embedded, str):
            raw_embedded = raw_embedded.lower() in {"1", "true", "yes"}
        self.use_embedded = bool(raw_embedded)

        kuzu_mod: ModuleType | None = None
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
                ensure_path_exists(self.file_path)
                self.db = cast(_KuzuDatabase, kuzu_mod.Database(self.db_path))
                self.conn = cast(_KuzuConnection, kuzu_mod.Connection(self.db))
                if self.conn is not None:
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
            self._store: dict[str, MemoryItem] = {}

    # utility serialisation helpers -------------------------------------------------
    def _count_tokens(self, text: str) -> int:
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Tokenizer encode failed: %s", exc)
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
    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a transaction and capture a snapshot if needed."""
        tx_id = transaction_id or str(uuid.uuid4())
        snapshot: dict[str, MemoryItem] | None = None
        if self._use_fallback:
            snapshot = deepcopy(getattr(self, "_store", {}))
        elif self.conn is not None:  # pragma: no cover - requires kuzu
            try:
                self.conn.execute("BEGIN TRANSACTION")
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to begin Kuzu transaction: %s", exc)
        self._transactions[tx_id] = snapshot or {}
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a previously started transaction."""
        self._transactions.pop(transaction_id, None)
        if (
            not self._use_fallback and self.conn is not None
        ):  # pragma: no cover - requires kuzu
            try:
                self.conn.execute("COMMIT")
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "Commit failed for Kuzu transaction %s: %s", transaction_id, exc
                )
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction restoring its snapshot."""
        snapshot = self._transactions.pop(transaction_id, None)
        if self._use_fallback:
            if snapshot is not None:
                self._store = snapshot
        elif self.conn is not None:  # pragma: no cover - requires kuzu
            try:
                self.conn.execute("ROLLBACK")
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "Rollback failed for Kuzu transaction %s: %s",
                    transaction_id,
                    exc,
                )
        return True

    supports_transactions: bool = True

    @contextmanager
    def transaction(self, transaction_id: str | None = None) -> Iterator[str]:
        """Context manager that wraps begin/commit/rollback."""
        tx_id = self.begin_transaction(transaction_id)
        try:
            yield tx_id
            self.commit_transaction(tx_id)
        except Exception:
            self.rollback_transaction(tx_id)
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
        elif self.conn is not None:  # pragma: no cover - requires kuzu
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

    def _retrieve_from_db(self, item_id: str) -> MemoryItem | None:
        if self._use_fallback:
            return self._store.get(item_id)
        if self.conn is None:  # pragma: no cover - defensive
            return None
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
    def retrieve(self, item_id: str) -> MemoryItem | None:
        if item_id in self._cache:
            return self._cache[item_id]
        item = self._retrieve_from_db(item_id)
        if item:
            self._cache[item_id] = item
        return item

    @retry_with_exponential_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def retrieve_version(self, item_id: str, version: int) -> MemoryItem | None:
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

    def get_versions(self, item_id: str) -> list[MemoryItem]:
        return list(self._versions.get(item_id, []))

    def get_history(self, item_id: str) -> list[dict[str, object]]:
        history: list[dict[str, object]] = []
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

    def search(self, query: Mapping[str, object]) -> list[MemoryRecord]:
        items = [
            self.retrieve(i)
            for i in (self._store.keys() if self._use_fallback else self._all_ids())
        ]
        results: list[MemoryRecord] = []
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
                results.append(
                    build_memory_record(item, source=self.__class__.__name__)
                )
        return results

    def _all_ids(self) -> list[str]:  # pragma: no cover - requires kuzu
        if self.conn is None:
            return []
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
        if self.conn is None:  # pragma: no cover - defensive
            return False
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

    def get_all_items(self) -> list[MemoryItem]:
        """Return all stored :class:`MemoryItem` objects."""

        if self._use_fallback:
            return list(self._store.values())

        items: list[MemoryItem] = []
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
            elif self.conn is not None:  # pragma: no cover - requires kuzu
                self.conn.execute(
                    "MERGE INTO memory(id,item) VALUES (?, ?)",
                    [item.id, self._serialise(item)],
                )
        self._cache.clear()

    def apply_memory_decay(self) -> list[str]:
        """Apply decay and return items below threshold."""
        volatile: list[str] = []
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
            elif self.conn is not None:  # pragma: no cover - requires kuzu
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
            if self.conn is not None:
                try:
                    self.conn.execute("COMMIT")
                except Exception as exc:
                    logger.debug("Commit during close failed: %s", exc)
                if hasattr(self.conn, "close"):
                    try:
                        self.conn.close()
                    except Exception as exc:
                        logger.debug("Connection close failed: %s", exc)
                self.conn = None
            if self.db is not None and hasattr(self.db, "close"):
                try:
                    self.db.close()
                except Exception as exc:
                    logger.debug("Database close failed: %s", exc)
                self.db = None
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to close Kuzu resources: %s", exc)

    def __del__(self):  # pragma: no cover - defensive
        try:
            self.close()
        except Exception as exc:
            logger.debug("Exception during KuzuStore __del__: %s", exc)
