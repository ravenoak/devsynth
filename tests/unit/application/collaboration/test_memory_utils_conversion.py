import pytest

from devsynth.application.collaboration.agent_collaboration import CollaborationTask
from devsynth.application.collaboration.collaboration_memory_utils import (
    from_memory_item,
    to_memory_item,
)
from devsynth.domain.models.memory import MemoryType


@pytest.mark.fast
def test_task_round_trip_to_memory_item() -> None:
    """ReqID: N/A"""

    task = CollaborationTask("type", "desc", {"x": 1})
    item = to_memory_item(task, MemoryType.COLLABORATION_TASK)
    restored = from_memory_item(item)
    assert isinstance(restored, CollaborationTask)
    assert restored.id == task.id
