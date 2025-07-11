import os
import json
import uuid
import pytest
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from devsynth.domain.models.memory import MemoryItem, MemoryType
try:
    from devsynth.application.memory.lmdb_store import LMDBStore
except ImportError:
    LMDBStore = None
from devsynth.exceptions import MemoryStoreError
pytestmark = pytest.mark.requires_resource('lmdb')


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
        if os.path.exists(os.path.join(temp_dir, 'memory.lmdb')):
            shutil.rmtree(os.path.join(temp_dir, 'memory.lmdb'))

    def test_init_succeeds(self, store, temp_dir):
        """Test initialization of LMDBStore.

ReqID: N/A"""
        assert store.base_path == temp_dir
        assert store.db_path == os.path.join(temp_dir, 'memory.lmdb')
        assert store.token_count == 0

    def test_store_and_retrieve_succeeds(self, store):
        """Test storing and retrieving a memory item.

ReqID: N/A"""
        item = MemoryItem(id='', content='Test content', memory_type=
            MemoryType.SHORT_TERM, metadata={'key': 'value'}, created_at=
            datetime.now())
        item_id = store.store(item)
        assert item_id
        assert item.id == item_id
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == 'Test content'
        assert retrieved_item.memory_type == MemoryType.SHORT_TERM
        assert retrieved_item.metadata == {'key': 'value'}
        assert isinstance(retrieved_item.created_at, datetime)

    def test_retrieve_nonexistent_succeeds(self, store):
        """Test retrieving a nonexistent memory item.

ReqID: N/A"""
        retrieved_item = store.retrieve('nonexistent')
        assert retrieved_item is None

    def test_search_succeeds(self, store):
        """Test searching for memory items.

ReqID: N/A"""
        items = [MemoryItem(id='', content='Content 1', memory_type=
            MemoryType.SHORT_TERM, metadata={'key': 'value1', 'tag': 'test'
            }, created_at=datetime.now()), MemoryItem(id='', content=
            'Content 2', memory_type=MemoryType.LONG_TERM, metadata={'key':
            'value2', 'tag': 'test'}, created_at=datetime.now()),
            MemoryItem(id='', content='Content 3', memory_type=MemoryType.
            SHORT_TERM, metadata={'key': 'value3', 'tag': 'other'},
            created_at=datetime.now())]
        for item in items:
            store.store(item)
        results = store.search({'memory_type': MemoryType.SHORT_TERM})
        assert len(results) == 2
        assert all(item.memory_type == MemoryType.SHORT_TERM for item in
            results)
        results = store.search({'metadata.tag': 'test'})
        assert len(results) == 2
        assert all(item.metadata.get('tag') == 'test' for item in results)
        results = store.search({'content': 'Content 2'})
        assert len(results) == 1
        assert results[0].content == 'Content 2'
        results = store.search({'memory_type': MemoryType.SHORT_TERM,
            'metadata.tag': 'test'})
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.SHORT_TERM
        assert results[0].metadata.get('tag') == 'test'

    def test_delete_succeeds(self, store):
        """Test deleting a memory item.

ReqID: N/A"""
        item = MemoryItem(id='', content='Test content', memory_type=
            MemoryType.SHORT_TERM, metadata={'key': 'value'}, created_at=
            datetime.now())
        item_id = store.store(item)
        assert store.retrieve(item_id) is not None
        result = store.delete(item_id)
        assert result is True
        assert store.retrieve(item_id) is None
        result = store.delete('nonexistent')
        assert result is False

    def test_token_usage_succeeds(self, store):
        """Test token usage tracking.

ReqID: N/A"""
        assert store.get_token_usage() == 0
        item = MemoryItem(id='', content='Test content', memory_type=
            MemoryType.SHORT_TERM, metadata={'key': 'value'}, created_at=
            datetime.now())
        store.store(item)
        assert store.get_token_usage() > 0
        store.retrieve(item.id)
        assert store.get_token_usage() > 0

    def test_persistence_succeeds(self, temp_dir):
        """Test that data persists between store instances.

ReqID: N/A"""
        store1 = LMDBStore(temp_dir)
        item = MemoryItem(id='', content='Test content', memory_type=
            MemoryType.SHORT_TERM, metadata={'key': 'value'}, created_at=
            datetime.now())
        item_id = store1.store(item)
        store1.close()
        store2 = LMDBStore(temp_dir)
        retrieved_item = store2.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == 'Test content'
        store2.close()

    def test_close_and_reopen_succeeds(self, store, temp_dir):
        """Test closing and reopening the store.

ReqID: N/A"""
        item = MemoryItem(id='', content='Test content', memory_type=
            MemoryType.SHORT_TERM, metadata={'key': 'value'}, created_at=
            datetime.now())
        item_id = store.store(item)
        store.close()
        store = LMDBStore(temp_dir)
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == 'Test content'

    def test_transaction_isolation_succeeds(self, store):
        """Test that transactions are isolated.

ReqID: N/A"""
        with store.begin_transaction() as txn:
            item = MemoryItem(id='', content='Transaction test',
                memory_type=MemoryType.SHORT_TERM, metadata={'key': 'value'
                }, created_at=datetime.now())
            item_id = store.store_in_transaction(txn, item)
            retrieved_item = store.retrieve_in_transaction(txn, item_id)
            assert retrieved_item is not None
            assert retrieved_item.content == 'Transaction test'
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.content == 'Transaction test'

    def test_transaction_abort_succeeds(self, store):
        """Test that aborted transactions don't persist changes.

ReqID: N/A"""
        item1 = MemoryItem(id='', content='Outside transaction',
            memory_type=MemoryType.SHORT_TERM, metadata={'key': 'value1'},
            created_at=datetime.now())
        item1_id = store.store(item1)
        try:
            with store.begin_transaction() as txn:
                item2 = MemoryItem(id='', content='Inside transaction',
                    memory_type=MemoryType.SHORT_TERM, metadata={'key':
                    'value2'}, created_at=datetime.now())
                item2_id = store.store_in_transaction(txn, item2)
                item1.content = 'Modified in transaction'
                store.store_in_transaction(txn, item1)
                assert store.retrieve_in_transaction(txn, item1_id
                    ).content == 'Modified in transaction'
                assert store.retrieve_in_transaction(txn, item2_id) is not None
                raise ValueError('Abort transaction')
        except ValueError:
            pass
        assert store.retrieve(item2_id) is None
        assert store.retrieve(item1_id).content == 'Outside transaction'
