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


def test_persistence_across_restarts(tmp_path):
    """Synchronizer preserves data across store re-instantiation.

    ReqID: complete-memory-system-integration
    """

    manager = SynchronizationManager(base_path=str(tmp_path))
    item = MemoryItem(
        id=str(uuid.uuid4()),
        content="round trip",
        memory_type=MemoryType.LONG_TERM,
    )
    item_id = manager.store(item)

    # Recreate manager with same base path to verify persistence
    new_manager = SynchronizationManager(base_path=str(tmp_path))
    retrieved = new_manager.retrieve(item_id)
    assert retrieved is not None
    assert retrieved.content == "round trip"
