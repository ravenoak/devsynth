import logging
from datetime import datetime

import pytest

from devsynth.application.collaboration.collaborative_wsde_team import (
    CollaborativeWSDETeam,
)
from devsynth.application.memory.memory_manager import MemoryManager
from tests.conftest import is_resource_available
from tests.fixtures.resources import (
    OPTIONAL_BACKEND_REQUIREMENTS,
    backend_import_reason,
    backend_skip_reason,
)


class DummyAgent:
    def __init__(self, name: str):
        self.name = name
        self.expertise = ["general"]
        self.current_role = None


class RoleTeam(CollaborativeWSDETeam):
    def __init__(self, memory_manager: MemoryManager):
        super().__init__("team", memory_manager=memory_manager)
        self.agents = [DummyAgent("a1"), DummyAgent("a2")]
        self.logger = logging.getLogger("test")

    def dynamic_role_reassignment(self, task):
        self.agents[0].current_role = "Primus"
        self.agents[1].current_role = "Scribe"

    def get_primus(self):
        for agent in self.agents:
            if agent.current_role == "Primus":
                return agent
        return None

    def get_messages(self, agent=None, filters=None):
        now = datetime.now()
        return [{"timestamp": now, "content": {"opinion": "approve", "rationale": "r"}}]

    def _generate_agent_opinions(self, task):
        pass

    def _identify_conflicts(self, task):
        return []

    def _identify_weighted_majority_opinion(self, opinions, keywords):
        return "approve"

    def _generate_stakeholder_explanation(self, task, result):
        return "because"

    def vote_on_critical_decision(self, task):
        return self.build_consensus(task)


@pytest.mark.slow
@pytest.mark.requires_resource("lmdb")
@pytest.mark.requires_resource("faiss")
@pytest.mark.requires_resource("kuzu")
def test_role_reassignment_shared_memory(tmp_path):
    extras_map = {
        name: tuple(OPTIONAL_BACKEND_REQUIREMENTS[name]["extras"])
        for name in ("lmdb", "faiss", "kuzu")
    }

    for resource, extras in extras_map.items():
        if not is_resource_available(resource):
            pytest.skip(backend_skip_reason(resource, extras))

    lmdb_mod = pytest.importorskip(
        "lmdb",
        reason=backend_import_reason("lmdb"),
    )
    pytest.importorskip(
        "faiss",
        reason=backend_import_reason("faiss"),
    )
    pytest.importorskip(
        "kuzu",
        reason=backend_import_reason("kuzu"),
    )

    if not hasattr(lmdb_mod, "open"):
        pytest.skip("lmdb unavailable")

    LMDBStore = pytest.importorskip(
        "devsynth.application.memory.lmdb_store",
        reason=backend_import_reason("lmdb"),
    ).LMDBStore
    FAISSStore = pytest.importorskip(
        "devsynth.application.memory.faiss_store",
        reason=backend_import_reason("faiss"),
    ).FAISSStore
    KuzuStore = pytest.importorskip(
        "devsynth.application.memory.kuzu_store",
        reason=backend_import_reason("kuzu"),
    ).KuzuStore

    class LMDBTestStore(LMDBStore):
        def is_transaction_active(self, transaction_id: str) -> bool:
            return False

    class KuzuTestStore(KuzuStore):
        def begin_transaction(self, transaction_id: str | None = None):
            return transaction_id or "0"

        def commit_transaction(self, transaction_id: str) -> bool:
            return True

        def rollback_transaction(self, transaction_id: str) -> bool:
            return True

        def is_transaction_active(self, transaction_id: str) -> bool:
            return False

    lmdb_store = LMDBTestStore(str(tmp_path / "lmdb"))
    faiss_store = FAISSStore(str(tmp_path / "faiss"))
    kuzu_store = KuzuTestStore(str(tmp_path / "kuzu"))
    mm = MemoryManager(
        adapters={"lmdb": lmdb_store, "faiss": faiss_store, "kuzu": kuzu_store}
    )
    team = RoleTeam(mm)
    task = {"id": "t1", "title": "Test", "options": ["approve", "reject"]}

    team.vote_with_role_reassignment(task)

    for name, store in mm.adapters.items():
        if name == "faiss":
            assert any(
                m.get("metadata", {}).get("type") == "CONSENSUS_VECTOR"
                for m in store.metadata.values()
            )
        else:
            results = store.search({"metadata.type": "CONSENSUS_DECISION"})
            assert results
