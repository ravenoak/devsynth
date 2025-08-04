from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.context_manager import InMemoryStore, SimpleContextManager
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.agents.wsde_memory_integration import WSDEMemoryIntegration
from devsynth.domain.models.wsde import WSDETeam
from devsynth.domain.models.memory import MemoryType
from devsynth.application.collaboration.peer_review import PeerReview
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.context_manager import InMemoryStore, SimpleContextManager


class SimpleStore(InMemoryStore):
    def begin_transaction(self, *args, **kwargs):
        return None

    def commit_transaction(self, *args, **kwargs):
        return True

    def rollback_transaction(self, *args, **kwargs):
        return False

    def is_transaction_active(self) -> bool:
        return False


def test_store_and_retrieve_solution_by_phase_succeeds(tmp_path):
    """Test that store and retrieve solution by phase succeeds.

ReqID: N/A"""
    store = SimpleStore()
    adapter = MemorySystemAdapter(memory_store=store, context_manager=
        SimpleContextManager(), create_paths=False)
    manager = MemoryManager(adapters={'default': adapter})
    team = WSDETeam(name='TestWsdeMemoryEdrrIntegrationTeam')
    wsde_memory = WSDEMemoryIntegration(adapter, team)
    task = {'id': 'task1', 'description': 'demo'}
    solution = {'id': 'sol1', 'content': 's'}
    wsde_memory.store_agent_solution('agent1', task, solution, 'Expand')
    results = wsde_memory.retrieve_solutions_by_edrr_phase('task1', 'Expand')
    assert len(results) == 1
    assert results[0].metadata.get('edrr_phase') == 'Expand'


def test_cross_store_sync_and_peer_review_workflow(tmp_path):
    """Verify cross-store synchronization and peer-review persistence."""
    primary = SimpleStore()
    secondary = SimpleStore()
    adapter1 = MemorySystemAdapter(
        memory_store=primary, context_manager=SimpleContextManager(), create_paths=False
    )
    adapter2 = MemorySystemAdapter(
        memory_store=secondary, context_manager=SimpleContextManager(), create_paths=False
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
        work_product={"text": "wp"},
        author=author,
        reviewers=reviewers,
        memory_manager=manager,
    )
    review.assign_reviews()
    review.collect_reviews()
    review.finalize(approved=True)
    manager.flush_updates()

    def has_review(store):
        return any(item.memory_type == MemoryType.PEER_REVIEW for item in store.items.values())

    assert has_review(primary)
    assert has_review(secondary)
