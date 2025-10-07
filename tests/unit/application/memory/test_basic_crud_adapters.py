"""Basic CRUD lifecycle tests for optional memory backends."""

from __future__ import annotations

from datetime import datetime
from typing import NamedTuple

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType
from tests.fixtures.resources import backend_import_reason, resource_flag_enabled


class StoreCase(NamedTuple):
    """Describe how to construct a memory store for parametrized tests."""

    module: str
    class_name: str
    resource: str
    require_flag: bool


STORE_CASES = [
    pytest.param(
        StoreCase(
            "devsynth.application.memory.tinydb_store",
            "TinyDBStore",
            "tinydb",
            False,
        ),
        marks=pytest.mark.requires_resource("tinydb"),
        id="tinydb",
    ),
    pytest.param(
        StoreCase(
            "devsynth.application.memory.lmdb_store",
            "LMDBStore",
            "lmdb",
            False,
        ),
        marks=pytest.mark.requires_resource("lmdb"),
        id="lmdb",
    ),
    pytest.param(
        StoreCase(
            "devsynth.application.memory.kuzu_store",
            "KuzuStore",
            "kuzu",
            True,
        ),
        marks=pytest.mark.requires_resource("kuzu"),
        id="kuzu",
    ),
    pytest.param(
        StoreCase(
            "devsynth.application.memory.chromadb_store",
            "ChromaDBStore",
            "chromadb",
            True,
        ),
        marks=pytest.mark.requires_resource("chromadb"),
        id="chromadb",
    ),
]


def _load_store_class(case: StoreCase):
    """Import the requested store class, skipping if it is unavailable."""

    module = pytest.importorskip(
        case.module,
        reason=backend_import_reason(case.resource),
    )
    try:
        return getattr(module, case.class_name)
    except AttributeError as exc:  # pragma: no cover - defensive guard
        pytest.skip(f"Store class {case.class_name} missing: {exc}")


def _make_store(case: StoreCase, tmp_path, monkeypatch):
    """Instantiate a store with resource gating and in-test safeguards."""

    if case.require_flag and not resource_flag_enabled(case.resource):
        pytest.skip(
            "Resource '%s' disabled via DEVSYNTH_RESOURCE_%s_AVAILABLE"
            % (case.resource, case.resource.upper())
        )

    store_cls = _load_store_class(case)

    if case.class_name == "TinyDBStore":
        return store_cls(str(tmp_path))
    if case.class_name == "LMDBStore":
        return store_cls(str(tmp_path))
    if case.class_name == "KuzuStore":
        monkeypatch.setattr(store_cls, "__abstractmethods__", frozenset())
        return store_cls(str(tmp_path))
    if case.class_name == "ChromaDBStore":
        monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
        monkeypatch.setenv("ENABLE_CHROMADB", "1")
        return store_cls(str(tmp_path))

    raise ValueError(f"Unsupported store configuration: {case}")


@pytest.mark.parametrize("case", STORE_CASES)
@pytest.mark.medium
def test_basic_crud_lifecycle(case: StoreCase, tmp_path, monkeypatch):
    """All supported stores should satisfy the CRUD lifecycle contract."""

    store = _make_store(case, tmp_path, monkeypatch)
    try:
        item_id = (
            "test-item" if case.class_name in {"KuzuStore", "ChromaDBStore"} else ""
        )
        item = MemoryItem(
            id=item_id,
            content="hello",
            memory_type=MemoryType.WORKING,
            metadata={},
            created_at=datetime.now(),
        )

        created_id = store.store(item)
        assert created_id

        retrieved = store.retrieve(created_id)
        assert retrieved and retrieved.content == "hello"

        item.content = "updated"
        store.store(item)
        updated = store.retrieve(created_id)
        assert updated and updated.content == "updated"

        assert store.delete(created_id) is True
        assert store.retrieve(created_id) is None
    finally:
        if hasattr(store, "close"):
            store.close()
