import logging
from datetime import datetime

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast

# Optional dependencies
lmdb_mod = pytest.importorskip("lmdb")
pytest.importorskip("faiss")

from devsynth.application.collaboration.collaborative_wsde_team import (
    CollaborativeWSDETeam,
)
from devsynth.application.memory.faiss_store import FAISSStore
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.application.memory.lmdb_store import LMDBStore
from devsynth.application.memory.memory_manager import MemoryManager

if not hasattr(lmdb_mod, "open"):
    pytest.skip("lmdb unavailable", allow_module_level=True)

scenarios(feature_path(__file__, "general", "role_reassignment_shared_memory.feature"))


class DummyAgent:
    def __init__(self, name: str):
        self.name = name
        self.expertise = ["general"]
        self.current_role = None


class RoleTeam(CollaborativeWSDETeam):
    def __init__(self, memory_manager: MemoryManager):
        super().__init__("bdd-team", memory_manager=memory_manager)
        self.agents = [DummyAgent("a1"), DummyAgent("a2")]
        self.messages = {}
        self.logger = logging.getLogger("bdd")

    def dynamic_role_reassignment(
        self, task
    ):  # pragma: no cover - exercised in feature
        self.agents[0].current_role = "Primus"
        self.agents[1].current_role = "Scribe"

    def get_primus(self):  # pragma: no cover - simple selection
        for agent in self.agents:
            if agent.current_role == "Primus":
                return agent
        return None

    def get_messages(
        self, agent=None, filters=None
    ):  # pragma: no cover - basic opinions
        now = datetime.now()
        return [{"timestamp": now, "content": {"opinion": "approve", "rationale": "r"}}]

    def _generate_agent_opinions(self, task):  # pragma: no cover - not needed
        pass

    def _identify_conflicts(self, task):  # pragma: no cover - no conflicts
        return []

    def _identify_weighted_majority_opinion(
        self, opinions, keywords
    ):  # pragma: no cover - simple
        return "approve"

    def _generate_stakeholder_explanation(
        self, task, result
    ):  # pragma: no cover - simple
        return "because"

    def vote_on_critical_decision(
        self, task
    ):  # pragma: no cover - delegate to consensus
        return self.build_consensus(task)


@pytest.fixture
def context(tmp_path):
    class Context:
        pass

    class LMDBTestStore(LMDBStore):
        def is_transaction_active(
            self, transaction_id: str
        ) -> bool:  # pragma: no cover - simple
            return False

    class KuzuTestStore(KuzuStore):
        def begin_transaction(
            self, transaction_id: str | None = None
        ):  # pragma: no cover - simple
            return transaction_id or "0"

        def commit_transaction(
            self, transaction_id: str
        ) -> bool:  # pragma: no cover - simple
            return True

        def rollback_transaction(
            self, transaction_id: str
        ) -> bool:  # pragma: no cover - simple
            return True

        def is_transaction_active(
            self, transaction_id: str
        ) -> bool:  # pragma: no cover - simple
            return False

    lmdb_store = LMDBTestStore(str(tmp_path / "lmdb"))
    faiss_store = FAISSStore(str(tmp_path / "faiss"))
    kuzu_store = KuzuTestStore(str(tmp_path / "kuzu"))
    mm = MemoryManager(
        adapters={"lmdb": lmdb_store, "faiss": faiss_store, "kuzu": kuzu_store}
    )
    ctx = Context()
    ctx.team = RoleTeam(mm)
    ctx.mm = mm
    return ctx


@given("a collaborative WSDE team with LMDB, FAISS, and Kuzu stores")
def given_team(context):
    assert context.team


@when("the team reassigns roles and reaches consensus on a task")
def when_reassign_and_consensus(context):
    context.team.vote_with_role_reassignment(
        {"id": "t1", "title": "Test", "options": ["approve", "reject"]}
    )


@then("the consensus decision is persisted across LMDB, FAISS, and Kuzu")
def then_persisted(context):
    mm = context.mm
    for name, store in mm.adapters.items():
        if name == "faiss":
            assert any(
                m.get("metadata", {}).get("type") == "CONSENSUS_VECTOR"
                for m in store.metadata.values()
            )
        else:
            results = store.search({"metadata.type": "CONSENSUS_DECISION"})
            assert results
