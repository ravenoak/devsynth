import logging
from datetime import datetime

import pytest

from devsynth.application.collaboration.collaborative_wsde_team import (
    CollaborativeWSDETeam,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem


class DummyAgent:
    def __init__(self, name: str):
        self.name = name
        self.metadata = {"expertise": ["general"]}


class SimpleStore(MemoryStore):
    def __init__(self):
        self.items = {}

    def store(self, item: MemoryItem):
        if not item.id:
            item.id = str(len(self.items))
        self.items[item.id] = item
        return item.id

    def retrieve(self, item_id: str):
        return self.items.get(item_id)

    def search(self, query):  # pragma: no cover - unused in tests
        return list(self.items.values())

    def delete(self, item_id: str):  # pragma: no cover - unused in tests
        return self.items.pop(item_id, None) is not None

    def begin_transaction(self, *args, **kwargs):  # pragma: no cover - unused
        return None

    def commit_transaction(self, *args, **kwargs):  # pragma: no cover - unused
        return True

    def rollback_transaction(self, *args, **kwargs):  # pragma: no cover - unused
        return False

    def is_transaction_active(self):  # pragma: no cover - unused
        return False


class DemoTeam(CollaborativeWSDETeam):
    def __init__(self, memory_manager: MemoryManager):
        super().__init__("team", memory_manager=memory_manager)
        self.agents = [DummyAgent("a1"), DummyAgent("a2")]
        now = datetime.now()
        self.messages = {
            "a1": [
                {"timestamp": now, "content": {"opinion": "approve", "rationale": "r1"}}
            ],
            "a2": [
                {"timestamp": now, "content": {"opinion": "approve", "rationale": "r2"}}
            ],
        }
        self.logger = logging.getLogger("test")

    def get_messages(self, agent=None, filters=None):  # type: ignore[override]
        return self.messages.get(agent, [])

    def _generate_agent_opinions(self, task):  # pragma: no cover - not used
        pass

    def _identify_conflicts(self, task):  # type: ignore[override]
        return []

    def _identify_weighted_majority_opinion(self, opinions, keywords):
        return "approve"

    def _generate_stakeholder_explanation(self, task, consensus_result):
        return "because we agree"


@pytest.mark.slow
def test_consensus_syncs_across_stores():
    memory_manager = MemoryManager(adapters={"s1": SimpleStore(), "s2": SimpleStore()})
    team = DemoTeam(memory_manager)
    task = {"id": "t1", "title": "Test"}

    team.build_consensus(task)

    for store in memory_manager.adapters.values():
        types = [item.metadata.get("type") for item in store.items.values()]
        assert "CONSENSUS_DECISION" in types
        assert "CONSENSUS_SUMMARY" in types
