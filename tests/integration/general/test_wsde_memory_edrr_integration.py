import sys

import pytest

from tests.conftest import is_resource_available
from tests.fixtures.resources import (
    OPTIONAL_BACKEND_REQUIREMENTS,
    backend_skip_reason,
    skip_module_if_backend_disabled,
)

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.agents.wsde_memory_integration import WSDEMemoryIntegration
from devsynth.application.collaboration.peer_review import PeerReview
from devsynth.application.collaboration.structures import ReviewCycleSpec
from devsynth.application.memory.context_manager import (
    InMemoryStore,
    SimpleContextManager,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam


def _require_backend(resource: str) -> None:
    skip_module_if_backend_disabled(resource)
    extras = tuple(OPTIONAL_BACKEND_REQUIREMENTS[resource]["extras"])
    if not is_resource_available(resource):
        pytest.skip(
            backend_skip_reason(resource, extras),
            allow_module_level=False,
        )




class SimpleStore(InMemoryStore):
    def begin_transaction(self, *args, **kwargs):
        return None

    def commit_transaction(self, *args, **kwargs):
        return True

    def rollback_transaction(self, *args, **kwargs):
        return False

    def is_transaction_active(self) -> bool:
        return False


@pytest.mark.slow
def test_store_and_retrieve_solution_by_phase_succeeds(tmp_path):
    """Test that store and retrieve solution by phase succeeds.

    ReqID: N/A"""
    store = SimpleStore()
    adapter = MemorySystemAdapter(
        memory_store=store, context_manager=SimpleContextManager(), create_paths=False
    )
    manager = MemoryManager(adapters={"default": adapter})
    team = WSDETeam(name="TestWsdeMemoryEdrrIntegrationTeam")
    wsde_memory = WSDEMemoryIntegration(adapter, team)
    task = {"id": "task1", "description": "demo"}
    solution = {"id": "sol1", "content": "s"}
    wsde_memory.store_agent_solution("agent1", task, solution, "Expand")
    results = wsde_memory.retrieve_solutions_by_edrr_phase("task1", "Expand")
    assert len(results) == 1
    assert results[0].metadata.get("edrr_phase") == "Expand"


@pytest.mark.slow
def test_cross_store_sync_and_peer_review_workflow(tmp_path):
    """Verify cross-store synchronization and peer-review persistence."""
    primary = SimpleStore()
    secondary = SimpleStore()
    adapter1 = MemorySystemAdapter(
        memory_store=primary, context_manager=SimpleContextManager(), create_paths=False
    )
    adapter2 = MemorySystemAdapter(
        memory_store=secondary,
        context_manager=SimpleContextManager(),
        create_paths=False,
    )
    manager = MemoryManager(adapters={"tinydb": adapter1, "graph": adapter2})
    team = WSDETeam(name="SyncTeam")
    wsde_memory = WSDEMemoryIntegration(adapter1, team, memory_manager=manager)

    task = {"id": "task1", "description": "demo"}
    solution = {"id": "sol1", "content": "s"}
    wsde_memory.store_agent_solution("agent1", task, solution, "Expand")
    manager.flush_updates()

    def has_solution(store):
        return any(
            item.metadata.get("solution_id") == "sol1" for item in store.items.values()
        )

    assert has_solution(primary)
    assert has_solution(secondary)

    # Remove the solution from the primary store to test cross-store retrieval
    for sid, itm in list(primary.items.items()):
        if itm.metadata.get("solution_id") == "sol1":
            del primary.items[sid]

    # Retrieval should still succeed via the secondary store
    retrieved = wsde_memory.retrieve_agent_solutions("task1")
    assert any(r.metadata.get("solution_id") == "sol1" for r in retrieved)

    class SimpleAgent:
        def __init__(self, name):
            self.name = name

        def process(self, _):
            return {"feedback": f"feedback from {self.name}"}

    author = SimpleAgent("author")
    reviewers = [SimpleAgent("rev1"), SimpleAgent("rev2")]
    review = PeerReview(
        cycle=ReviewCycleSpec(
            work_product={"text": "wp"},
            author=author,
            reviewers=reviewers,
            memory_manager=manager,
        )
    )
    review.assign_reviews()
    review.collect_reviews()
    review.finalize(approved=True)
    manager.flush_updates()

    def has_review(store):
        return any(
            item.memory_type == MemoryType.PEER_REVIEW for item in store.items.values()
        )

    assert has_review(primary)
    assert has_review(secondary)


@pytest.mark.requires_resource("lmdb")
@pytest.mark.requires_resource("faiss")
@pytest.mark.requires_resource("kuzu")
@pytest.mark.requires_resource("chromadb")
@pytest.mark.slow
def test_sync_manager_coordinated_backends(tmp_path, monkeypatch):
    """Ensure SyncManager synchronizes LMDB, FAISS and Kuzu stores."""

    for backend in ("lmdb", "faiss", "kuzu", "chromadb"):
        _require_backend(backend)

    LMDBStore = pytest.importorskip("devsynth.application.memory.lmdb_store").LMDBStore
    FAISSStore = pytest.importorskip(
        "devsynth.application.memory.faiss_store"
    ).FAISSStore
    from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
    from devsynth.application.memory.sync_manager import SyncManager
    from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

    monkeypatch.delitem(sys.modules, "kuzu", raising=False)
    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))
    try:
        from devsynth.application.memory.kuzu_store import KuzuStore
    except Exception:  # pragma: no cover - optional
        KuzuStore = None

    for cls in (KuzuMemoryStore, LMDBStore, FAISSStore, KuzuStore):
        if cls is not None:
            try:
                cls.__abstractmethods__ = frozenset()
            except Exception:
                pass
    lmdb_store = LMDBStore(str(tmp_path / "lmdb"))
    faiss_store = FAISSStore(str(tmp_path / "faiss"))
    kuzu_store = KuzuMemoryStore.create_ephemeral(use_provider_system=False)

    manager = MemoryManager(
        adapters={"lmdb": lmdb_store, "faiss": faiss_store, "kuzu": kuzu_store}
    )
    manager.sync_manager = SyncManager(manager)

    item = MemoryItem(id="x", content="hello", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="x", content="hello", embedding=[0.1] * 5, metadata={})

    lmdb_store.store(item)
    faiss_store.store_vector(vector)

    manager.synchronize("lmdb", "kuzu")
    manager.synchronize("faiss", "kuzu")

    assert kuzu_store.retrieve("x") is not None
    assert kuzu_store.vector.retrieve_vector("x") is not None
