import uuid

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.memory.sync_manager import SynchronizationManager

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("tinydb"),
    pytest.mark.requires_resource("duckdb"),
    pytest.mark.requires_resource("lmdb"),
    pytest.mark.requires_resource("kuzu"),
]


def test_store_and_retrieve_across_adapters(tmp_path):
    """Items stored through the manager persist across all backends.

    ReqID: complete-memory-system-integration
    """

    manager = SynchronizationManager(base_path=str(tmp_path))
    item = MemoryItem(
        id=str(uuid.uuid4()),
        content="sync test",
        memory_type=MemoryType.SHORT_TERM,
    )
    item_id = manager.store(item)

    # Each backend should contain the item
    for store in manager.stores.values():
        retrieved = store.retrieve(item_id)
        assert retrieved is not None
        assert retrieved.content == "sync test"

    # Manager retrieval falls back across stores
    found = manager.retrieve(item_id)
    assert found is not None
    assert found.content == "sync test"
