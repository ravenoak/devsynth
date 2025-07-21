import types
from unittest.mock import MagicMock, patch
from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl


class SimpleAgent:

    def __init__(self, name, agent_type, expertise):
        self.name = name
        self.agent_type = agent_type
        self.current_role = None
        self.expertise = expertise
        self.config = types.SimpleNamespace(name=name, parameters={})
        self.process = MagicMock(return_value={'solution': name})


def test_delegate_task_calls_select_primus_by_expertise_and_updates_primus_succeeds(
    ):
    """Test that delegate task calls select primus by expertise and updates primus succeeds.

ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({'features': {'wsde_collaboration': 
        True}})
    doc = SimpleAgent('doc', 'docs', ['documentation', 'markdown'])
    coder = SimpleAgent('coder', 'code', ['python'])
    coordinator.add_agent(doc)
    coordinator.add_agent(coder)
    consensus = {'consensus': 'x', 'contributors': ['doc', 'coder'],
        'method': 'consensus_synthesis'}
    with patch.object(coordinator.team, 'build_consensus', return_value=
        consensus), patch.object(coordinator.team,
        'select_primus_by_expertise', wraps=coordinator.team.
        select_primus_by_expertise) as spy:
        result1 = coordinator.delegate_task({'team_task': True, 'type':
            'coding', 'language': 'python'})
        first_primus = coordinator.team.get_primus().name
        result2 = coordinator.delegate_task({'team_task': True, 'type':
            'documentation'})
        second_primus = coordinator.team.get_primus().name
    assert spy.call_count == 2
    assert first_primus == 'coder'
    assert second_primus == 'doc'
    assert result1['method'] == 'consensus_synthesis'
    assert result2['method'] == 'consensus_synthesis'


def test_primus_rotation_resets_after_all_have_served_succeeds():
    """Test that primus rotation resets after all have served succeeds.

ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({'features': {'wsde_collaboration': 
        True}})
    a1 = SimpleAgent('a1', 'code', ['python'])
    a2 = SimpleAgent('a2', 'docs', ['docs'])
    a3 = SimpleAgent('a3', 'test', ['testing'])
    coordinator.add_agent(a1)
    coordinator.add_agent(a2)
    coordinator.add_agent(a3)
    consensus = {'consensus': 'x', 'contributors': ['a1', 'a2', 'a3'],
        'method': 'consensus_synthesis'}
    with patch.object(coordinator.team, 'build_consensus', return_value=
        consensus):
        coordinator.delegate_task({'team_task': True, 'type': 'coding'})
        first = coordinator.team.get_primus().name
        coordinator.delegate_task({'team_task': True, 'type': 'documentation'})
        second = coordinator.team.get_primus().name
        coordinator.delegate_task({'team_task': True, 'type': 'testing'})
        third = coordinator.team.get_primus().name
        assert {first, second, third} == {'a1', 'a2', 'a3'}
        assert all(agent.has_been_primus for agent in coordinator.team.agents)
        coordinator.delegate_task({'team_task': True, 'type': 'coding'})
        reset = coordinator.team.get_primus().name
    assert reset == first
    others = [a for a in coordinator.team.agents if a.name != reset]
    assert all(not o.has_been_primus for o in others)
