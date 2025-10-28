import tempfile

import pytest

from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.adapters.vector_memory_adapter import (
    VectorMemoryAdapter,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.exceptions import MemoryTransactionError


@pytest.mark.parametrize("adapter_cls", [TinyDBMemoryAdapter, GraphMemoryAdapter])
@pytest.mark.medium
def test_store_retrieve_search_update(adapter_cls, tmp_path):
    """ReqID: FR-44"""
    if adapter_cls is GraphMemoryAdapter:
        adapter = adapter_cls(base_path=tmp_path)
    else:
        adapter = adapter_cls(db_path=str(tmp_path / "db.json"))
    item = MemoryItem(
        id="",
        content={"foo": "bar"},
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"tag": "t"},
    )
    item_id = adapter.store(item)
    retrieved = adapter.retrieve(item_id)
    assert retrieved is not None
    assert retrieved.content["foo"] == "bar"
    results = adapter.search({"tag": "t"})
    assert any(r.id == item_id for r in results)
    item.content = {"foo": "baz"}
    adapter.store(item)
    updated = adapter.retrieve(item_id)
    assert updated.content["foo"] == "baz"


@pytest.mark.medium
def test_vector_adapter_operations():
    """ReqID: FR-47"""
    adapter = VectorMemoryAdapter()
    vector = MemoryVector(
        id="", content="doc", embedding=[0.1, 0.2, 0.3], metadata={"kind": "test"}
    )
    vid = adapter.store_vector(vector)
    retrieved = adapter.retrieve_vector(vid)
    assert retrieved is not None
    assert retrieved.content == "doc"
    results = adapter.similarity_search([0.1, 0.2, 0.3], top_k=1)
    assert results and results[0].id == vid


@pytest.mark.medium
def test_tinydb_adapter_transaction_support(tmp_path):
    """Test transaction support in TinyDBMemoryAdapter.

    ReqID: FR-44
    """
    adapter = TinyDBMemoryAdapter(db_path=str(tmp_path / "db.json"))
    item1 = MemoryItem(
        id="test1",
        content="Test content 1",
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"tag": "transaction_test"},
    )
    item2 = MemoryItem(
        id="test2",
        content="Test content 2",
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"tag": "transaction_test"},
    )
    transaction_id = adapter.begin_transaction()
    # Should auto-generate an identifier when none is provided
    assert isinstance(transaction_id, str) and transaction_id
    adapter.store(item1, transaction_id=transaction_id)
    retrieved = adapter.retrieve(item1.id)
    assert retrieved is not None
    assert retrieved.content == "Test content 1"
    adapter.delete(item1.id, transaction_id=transaction_id)
    retrieved = adapter.retrieve(item1.id)
    assert retrieved is None
    adapter.store(item2, transaction_id=transaction_id)
    result = adapter.commit_transaction(transaction_id)
    assert result is True
    retrieved = adapter.retrieve(item2.id)
    assert retrieved is not None
    assert retrieved.content == "Test content 2"
    transaction_id2 = adapter.begin_transaction("tx2")
    item3 = MemoryItem(
        id="test3",
        content="Test content 3",
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"tag": "transaction_test"},
    )
    adapter.store(item3, transaction_id=transaction_id2)
    adapter.delete(item2.id, transaction_id=transaction_id2)
    assert adapter.retrieve(item3.id) is not None
    assert adapter.retrieve(item2.id) is None
    result = adapter.rollback_transaction(transaction_id2)
    assert result is True
    assert adapter.retrieve(item3.id) is None
    assert adapter.retrieve(item2.id) is not None
    with pytest.raises(MemoryTransactionError):
        adapter.store(item1, transaction_id="invalid_tx")
    with pytest.raises(MemoryTransactionError):
        adapter.delete(item1.id, transaction_id="invalid_tx")


@pytest.mark.medium
def test_tinydb_transaction_optional_id(tmp_path):
    """Ensure commit and rollback work without explicitly passing IDs.

    ReqID: FR-44
    """

    adapter = TinyDBMemoryAdapter(db_path=str(tmp_path / "db.json"))
    item = MemoryItem(
        id="a",
        content="A",
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"tag": "x"},
    )

    tx_id = adapter.begin_transaction()
    adapter.store(item, transaction_id=tx_id)
    # Commit without providing the transaction id
    assert adapter.commit_transaction() is True
    assert adapter.retrieve("a") is not None

    tx_id = adapter.begin_transaction()
    adapter.delete("a", transaction_id=tx_id)
    # Rollback without providing the transaction id
    assert adapter.rollback_transaction() is True
    assert adapter.retrieve("a") is not None

    # No active transaction should raise an error
    with pytest.raises(MemoryTransactionError):
        adapter.commit_transaction()
    with pytest.raises(MemoryTransactionError):
        adapter.rollback_transaction()


@pytest.mark.medium
def test_tinydb_serializes_unhandled_types(tmp_path):
    """ReqID: FR-44

    TinyDB adapter should gracefully handle metadata with non-JSON values."""

    from datetime import datetime

    adapter = TinyDBMemoryAdapter(db_path=str(tmp_path / "db.json"))
    item = MemoryItem(
        id="meta1",
        content="content",
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"tags": {"a", "b"}, "timestamp": datetime(2024, 1, 1)},
    )

    item_id = adapter.store(item)
    retrieved = adapter.retrieve(item_id)
    assert retrieved is not None
    # sets should round-trip as lists
    assert set(retrieved.metadata["tags"]) == {"a", "b"}
    # datetimes should round-trip as ISO strings
    assert retrieved.metadata["timestamp"] == datetime(2024, 1, 1).isoformat()
