from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.context_manager import InMemoryStore, SimpleContextManager
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.agents.wsde_memory_integration import WSDEMemoryIntegration
from devsynth.domain.models.wsde import WSDETeam


def test_store_and_retrieve_solution_by_phase_succeeds(tmp_path):
    """Test that store and retrieve solution by phase succeeds.

ReqID: N/A"""
    store = InMemoryStore()
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
