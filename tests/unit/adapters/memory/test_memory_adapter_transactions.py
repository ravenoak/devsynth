"""Tests for transaction-related error handling in ``MemorySystemAdapter``."""

import sys
import types

import pytest

pytestmark = [pytest.mark.memory_intensive, pytest.mark.isolation]


def _import_adapter():
    """Import ``memory_adapter`` with heavy dependencies patched out."""

    stubs = {
        "devsynth.config.settings": types.SimpleNamespace(
            get_settings=lambda: types.SimpleNamespace(
                memory_store_type="file",
                memory_file_path="/tmp",
                # Keep test lightweight by restricting context size
                max_context_size=10,
                context_expiration_days=1,
                vector_store_enabled=False,
                provider_type=None,
                chromadb_collection_name="test",
                chromadb_host=None,
                chromadb_port=8000,
                enable_chromadb=False,
                encryption_at_rest=False,
                encryption_key=None,
            ),
            ensure_path_exists=lambda path, create=True: path,
        ),
        "devsynth.application.memory.duckdb_store": types.SimpleNamespace(
            DuckDBStore=object
        ),
        "devsynth.application.memory.lmdb_store": types.SimpleNamespace(
            LMDBStore=object
        ),
        "devsynth.application.memory.faiss_store": types.SimpleNamespace(
            FAISSStore=object
        ),
        "devsynth.application.memory.rdflib_store": types.SimpleNamespace(
            RDFLibStore=object
        ),
        "devsynth.adapters.kuzu_memory_store": types.SimpleNamespace(
            KuzuMemoryStore=object
        ),
        "devsynth.adapters.memory.kuzu_adapter": types.SimpleNamespace(
            KuzuAdapter=object
        ),
    }
    for name, module in stubs.items():
        sys.modules.setdefault(name, module)

    from devsynth.adapters.memory.memory_adapter import (  # type: ignore
        MemoryStoreError,
        MemorySystemAdapter,
    )

    return MemorySystemAdapter, MemoryStoreError


class _DummyStore:
    """Minimal memory store without transaction support."""

    def store(self, item):  # pragma: no cover - unused in tests
        pass

    def retrieve(self, item_id):  # pragma: no cover - unused in tests
        return None

    def search(self, query):  # pragma: no cover - unused in tests
        return []

    def delete(self, item_id):  # pragma: no cover - unused in tests
        return True


class _DummyContext:
    """Simple context manager implementation for testing."""

    def add_to_context(self, key, value):  # pragma: no cover - unused in tests
        pass

    def get_from_context(self, key):  # pragma: no cover - unused in tests
        return None

    def get_full_context(self):  # pragma: no cover - unused in tests
        return {}

    def clear_context(self):  # pragma: no cover - unused in tests
        pass


def _make_adapter():
    """Create a ``MemorySystemAdapter`` with dummy components."""

    MemorySystemAdapter, _ = _import_adapter()
    return MemorySystemAdapter(
        memory_store=_DummyStore(),
        context_manager=_DummyContext(),
        vector_store=None,
    )


@pytest.mark.medium
def test_begin_transaction_unsupported_store_raises_error():
    """``begin_transaction`` should raise when store lacks transaction support."""

    _, MemoryStoreError = _import_adapter()
    adapter = _make_adapter()
    with pytest.raises(MemoryStoreError):
        adapter.begin_transaction()


@pytest.mark.medium
def test_commit_transaction_unsupported_store_raises_error():
    """``commit_transaction`` should raise when store lacks transaction support."""

    _, MemoryStoreError = _import_adapter()
    adapter = _make_adapter()
    with pytest.raises(MemoryStoreError):
        adapter.commit_transaction("txn")
