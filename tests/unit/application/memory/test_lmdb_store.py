import os
import shutil
import uuid
from datetime import datetime

import pytest

from tests.fixtures.resources import (
    backend_import_reason,
    skip_if_missing_backend,
    skip_module_if_backend_disabled,
)

skip_module_if_backend_disabled("lmdb")
pytest.importorskip("lmdb", reason=backend_import_reason("lmdb"))

pytestmark = skip_if_missing_backend("lmdb")

from devsynth.application.memory.dto import MemoryRecord
from devsynth.application.memory.lmdb_store import LMDBStore
from devsynth.domain.models.memory import MemoryItem, MemoryType


class TestLMDBStore:
    """Tests for the LMDBStore class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a LMDBStore instance for testing."""
        store = LMDBStore(temp_dir)
        yield store
        store.close()
        if os.path.exists(os.path.join(temp_dir, "memory.lmdb")):
            shutil.rmtree(os.path.join(temp_dir, "memory.lmdb"))

    @pytest.mark.medium
    def test_init_succeeds(self, store, temp_dir):
        """Test initialization of LMDBStore.

        ReqID: N/A"""
        assert store.base_path == temp_dir
        assert store.db_path == os.path.join(temp_dir, "memory.lmdb")
        assert store.token_count == 0

    @pytest.mark.medium
    def test_store_and_retrieve_succeeds(self, store):
        """Test storing and retrieving a memory item.

        ReqID: N/A"""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store.store(item)
        assert item_id
        assert item.id == item_id
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert isinstance(retrieved_item, MemoryItem)
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"
        assert retrieved_item.memory_type == MemoryType.SHORT_TERM
        assert retrieved_item.metadata == {"key": "value"}
        assert isinstance(retrieved_item.created_at, datetime)

    @pytest.mark.medium
    def test_retrieve_nonexistent_succeeds(self, store):
        """Test retrieving a nonexistent memory item.

        ReqID: N/A"""
        retrieved_item = store.retrieve("nonexistent")
        assert retrieved_item is None

    @pytest.mark.medium
    def test_search_succeeds(self, store):
        """Test searching for memory items.

        ReqID: N/A"""
        items = [
            MemoryItem(
                id="",
                content="Content 1",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value1", "tag": "test"},
                created_at=datetime.now(),
            ),
            MemoryItem(
                id="",
                content="Content 2",
                memory_type=MemoryType.LONG_TERM,
                metadata={"key": "value2", "tag": "test"},
                created_at=datetime.now(),
            ),
            MemoryItem(
                id="",
                content="Content 3",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value3", "tag": "other"},
                created_at=datetime.now(),
            ),
        ]
        for item in items:
            store.store(item)
        results = store.search({"memory_type": MemoryType.SHORT_TERM})
        assert isinstance(results, list)
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert len(results) == 2
        assert all(record.memory_type == MemoryType.SHORT_TERM for record in results)

        results = store.search({"metadata.tag": "test"})
        assert isinstance(results, list)
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert len(results) == 2
        assert all(record.metadata.get("tag") == "test" for record in results)

        results = store.search({"content": "Content 2"})
        assert isinstance(results, list)
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert len(results) == 1
        assert results[0].content == "Content 2"

        results = store.search(
            {"memory_type": MemoryType.SHORT_TERM, "metadata.tag": "test"}
        )
        assert isinstance(results, list)
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.SHORT_TERM
        assert results[0].metadata.get("tag") == "test"

    @pytest.mark.medium
    def test_delete_succeeds(self, store):
        """Test deleting a memory item.

        ReqID: N/A"""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store.store(item)
        assert store.retrieve(item_id) is not None
        result = store.delete(item_id)
        assert result is True
        assert store.retrieve(item_id) is None
        result = store.delete("nonexistent")
        assert result is False

    @pytest.mark.medium
    def test_token_usage_succeeds(self, store):
        """Test token usage tracking.

        ReqID: N/A"""
        assert store.get_token_usage() == 0
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        store.store(item)
        assert store.get_token_usage() > 0
        store.retrieve(item.id)
        assert store.get_token_usage() > 0

    @pytest.mark.medium
    def test_persistence_succeeds(self, temp_dir):
        """Test that data persists between store instances.

        ReqID: N/A"""
        store1 = LMDBStore(temp_dir)
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store1.store(item)
        store1.close()
        store2 = LMDBStore(temp_dir)
        retrieved_item = store2.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"
        store2.close()

    @pytest.mark.medium
    def test_close_and_reopen_succeeds(self, store, temp_dir):
        """Test closing and reopening the store.

        ReqID: N/A"""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store.store(item)
        store.close()
        store = LMDBStore(temp_dir)
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"

    @pytest.mark.medium
    def test_transaction_isolation_succeeds(self, store):
        """Test that transactions are isolated.

        ReqID: N/A"""
        with store.transaction() as txn:
            item = MemoryItem(
                id="",
                content="Transaction test",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value"},
                created_at=datetime.now(),
            )
            item_id = store.store_in_transaction(txn, item)
            retrieved_item = store.retrieve_in_transaction(txn, item_id)
            assert retrieved_item is not None
            assert retrieved_item.content == "Transaction test"
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.content == "Transaction test"

    @pytest.mark.medium
    def test_transaction_abort_succeeds(self, store):
        """Test that aborted transactions don't persist changes.

        ReqID: N/A"""
        item1 = MemoryItem(
            id="",
            content="Outside transaction",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value1"},
            created_at=datetime.now(),
        )
        item1_id = store.store(item1)
        try:
            with store.transaction() as txn:
                item2 = MemoryItem(
                    id="",
                    content="Inside transaction",
                    memory_type=MemoryType.SHORT_TERM,
                    metadata={"key": "value2"},
                    created_at=datetime.now(),
                )
                item2_id = store.store_in_transaction(txn, item2)
                item1.content = "Modified in transaction"
                store.store_in_transaction(txn, item1)
                assert (
                    store.retrieve_in_transaction(txn, item1_id).content
                    == "Modified in transaction"
                )
                assert store.retrieve_in_transaction(txn, item2_id) is not None
                raise ValueError("Abort transaction")
        except ValueError:
            pass
        assert store.retrieve(item2_id) is None
        assert store.retrieve(item1_id).content == "Outside transaction"

    @pytest.mark.fast
    def test_begin_transaction_tracks_and_cleans_up(self, store):
        """Ensure explicit transactions are tracked and removed on failure.

        ReqID: N/A"""

        transaction_id = str(uuid.uuid4())

        with pytest.raises(RuntimeError):
            with store.transaction(transaction_id=transaction_id):
                assert store.is_transaction_active(transaction_id)
                raise RuntimeError("abort for cleanup check")

        assert not store.is_transaction_active(transaction_id)

    @pytest.mark.fast
    def test_commit_transaction_persists_explicit_changes(self, store):
        """Explicit commits should persist data and clear tracking state.

        ReqID: N/A"""

        transaction_id = str(uuid.uuid4())
        txn = store.env.begin(write=True)
        store._transactions[transaction_id] = txn

        item = MemoryItem(
            id="",
            content="Explicit commit",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"scope": "commit"},
            created_at=datetime.now(),
        )
        item_id = store.store_in_transaction(txn, item)

        assert store.is_transaction_active(transaction_id)
        store.commit_transaction(transaction_id)

        assert not store.is_transaction_active(transaction_id)
        retrieved = store.retrieve(item_id)
        assert retrieved is not None
        assert retrieved.content == "Explicit commit"

    @pytest.mark.fast
    def test_rollback_transaction_discards_explicit_changes(self, store):
        """Explicit rollbacks should discard data and clear tracking state.

        ReqID: N/A"""

        transaction_id = str(uuid.uuid4())
        txn = store.env.begin(write=True)
        store._transactions[transaction_id] = txn

        item = MemoryItem(
            id="",
            content="Explicit rollback",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"scope": "rollback"},
            created_at=datetime.now(),
        )
        item_id = store.store_in_transaction(txn, item)

        assert store.is_transaction_active(transaction_id)
        store.rollback_transaction(transaction_id)

        assert not store.is_transaction_active(transaction_id)
        assert store.retrieve(item_id) is None

    @pytest.mark.fast
    def test_get_all_items_returns_everything(self, store):
        """get_all_items should surface each stored item exactly once.

        ReqID: N/A"""

        items = [
            MemoryItem(
                id="",
                content="First",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"order": 1},
                created_at=datetime.now(),
            ),
            MemoryItem(
                id="",
                content="Second",
                memory_type=MemoryType.LONG_TERM,
                metadata={"order": 2},
                created_at=datetime.now(),
            ),
        ]

        stored_ids = {store.store(item) for item in items}

        retrieved_items = store.get_all_items()

        assert {item.id for item in retrieved_items} == stored_ids
        assert {item.content for item in retrieved_items} == {"First", "Second"}
