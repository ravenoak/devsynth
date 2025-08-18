import logging
from datetime import datetime

import pytest

from devsynth.application.collaboration.wsde_team_consensus import (
    ConsensusBuildingMixin,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.interfaces.memory import MemoryStore


class DummyAgent:
    def __init__(self, name: str):
        self.name = name
        self.metadata = {"expertise": ["general"]}


class DummyTeam(ConsensusBuildingMixin):
    def __init__(self, memory_manager: MemoryManager):
        self.agents = [DummyAgent("a1"), DummyAgent("a2")]
        self.memory_manager = memory_manager
        self.tracked_decisions = {}
        self.logger = logging.getLogger("dummy")
        now = datetime.now()
        self.messages = {
            "a1": [
                {"timestamp": now, "content": {"opinion": "approve", "rationale": "r1"}}
            ],
            "a2": [
                {"timestamp": now, "content": {"opinion": "approve", "rationale": "r2"}}
            ],
        }

    def get_messages(self, agent=None, filters=None):
        return self.messages.get(agent, [])

    def _generate_agent_opinions(self, task):  # pragma: no cover - not used in tests
        pass

    def _identify_conflicts(self, task):
        return []

    def _identify_weighted_majority_opinion(self, opinions, keywords):
        return "approve"

    def _generate_stakeholder_explanation(self, task, consensus_result):
        return "because we agree"

    def send_message(self, *args, **kwargs):  # pragma: no cover - not used
        pass


@pytest.fixture
def memory_manager():
    class SimpleStore(MemoryStore):
        def __init__(self):
            self.items = {}

        def store(self, item):
            if not item.id:
                item.id = str(len(self.items))
            self.items[item.id] = item
            return item.id

        def retrieve(self, item_id):
            return self.items.get(item_id)

        def search(self, query):
            return list(self.items.values())

        def delete(self, item_id):
            return self.items.pop(item_id, None) is not None

        def begin_transaction(self, *args, **kwargs):
            return None

        def commit_transaction(self, *args, **kwargs):
            return True

        def rollback_transaction(self, *args, **kwargs):
            return False

        def is_transaction_active(self):
            return False

    return MemoryManager(adapters={"tinydb": SimpleStore(), "graph": SimpleStore()})


def test_build_consensus_stores_decision_and_summary(memory_manager):
    team = DummyTeam(memory_manager)
    task = {"id": "t1", "title": "Test"}
    team.build_consensus(task)
    for store in memory_manager.adapters.values():
        types = [item.metadata.get("type") for item in store.items.values()]
        assert "CONSENSUS_DECISION" in types
        assert "CONSENSUS_SUMMARY" in types


def test_summarize_voting_result_persists_summary(memory_manager):
    team = DummyTeam(memory_manager)
    voting_result = {
        "status": "completed",
        "result": "option_a",
        "vote_counts": {"option_a": 2},
    }
    summary = team.summarize_voting_result(voting_result)
    assert "option 'option_a' selected" in summary.lower()
    for store in memory_manager.adapters.values():
        assert any(
            item.metadata.get("type") == "VOTING_SUMMARY"
            for item in store.items.values()
        )
