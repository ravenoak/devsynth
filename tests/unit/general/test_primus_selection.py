import pytest
from unittest.mock import MagicMock
from devsynth.domain.models.wsde import WSDETeam


def create_agent(name: str, expertise: list[str]):
    agent = MagicMock()
    agent.name = name
    agent.expertise = expertise
    agent.current_role = None
    agent.has_been_primus = False
    return agent


@pytest.fixture
def rotation_team():
    """Team with two identical agents for deterministic rotation tests."""
    team = WSDETeam(name='TestPrimusSelectionTeam')
    a1 = create_agent('A1', ['python'])
    a2 = create_agent('A2', ['python'])
    team.add_agents([a1, a2])
    return team, a1, a2


@pytest.fixture
def weighted_team():
    """Team with a specialist and a generalist for expertise weighting."""
    team = WSDETeam(name='TestPrimusSelectionTeam')
    generalist = create_agent('Generalist', ['python'])
    specialist = create_agent('Specialist', ['python', 'backend'])
    team.add_agents([generalist, specialist])
    return team, generalist, specialist


@pytest.fixture
def documentation_team():
    """Team containing multiple documentation experts."""
    team = WSDETeam(name='TestPrimusSelectionTeam')
    coder = create_agent('Coder', ['python'])
    writer = create_agent('Writer', ['documentation'])
    doc = create_agent('Doc', ['documentation', 'markdown'])
    team.add_agents([coder, writer, doc])
    return team, coder, writer, doc


def test_highest_expertise_score_becomes_primus_succeeds():
    """Test that highest expertise score becomes primus succeeds.

ReqID: N/A"""
    team = WSDETeam(name='TestPrimusSelectionTeam')
    python_agent = create_agent('Python', ['python', 'backend'])
    js_agent = create_agent('JS', ['javascript', 'frontend'])
    tester = create_agent('Tester', ['testing'])
    team.add_agents([python_agent, js_agent, tester])
    task = {'type': 'coding', 'language': 'python', 'domain': 'backend'}
    team.select_primus_by_expertise(task)
    assert team.get_primus() is python_agent
    assert python_agent.has_been_primus


def test_prioritizes_agents_who_have_not_served_as_primus_succeeds():
    """Test that prioritizes agents who have not served as primus succeeds.

ReqID: N/A"""
    team = WSDETeam(name='TestPrimusSelectionTeam')
    python_agent = create_agent('Python', ['python'])
    doc_agent = create_agent('Doc', ['documentation', 'markdown'])
    team.add_agents([python_agent, doc_agent])
    task = {'type': 'coding', 'language': 'python'}
    team.select_primus_by_expertise(task)
    assert team.get_primus() is python_agent
    team.select_primus_by_expertise(task)
    assert team.get_primus() is doc_agent
    assert doc_agent.has_been_primus


def test_documentation_tasks_prefer_documentation_experts_succeeds():
    """Test that documentation tasks prefer documentation experts succeeds.

ReqID: N/A"""
    team = WSDETeam(name='TestPrimusSelectionTeam')
    coder = create_agent('Coder', ['python'])
    doc_agent = create_agent('Doc', ['documentation', 'markdown'])
    team.add_agents([coder, doc_agent])
    task = {'type': 'documentation', 'description': 'Update docs'}
    team.select_primus_by_expertise(task)
    assert team.get_primus() is doc_agent
    assert doc_agent.has_been_primus


def test_weighted_expertise_prefers_specialist_succeeds(weighted_team):
    """Test that weighted expertise prefers specialist succeeds.

ReqID: N/A"""
    team, generalist, specialist = weighted_team
    task = {'type': 'coding', 'language': 'python', 'domain': 'backend'}
    team.select_primus_by_expertise(task)
    assert team.get_primus() is specialist


def test_rotation_resets_after_all_agents_served_succeeds(rotation_team):
    """Test that rotation resets after all agents served succeeds.

ReqID: N/A"""
    team, a1, a2 = rotation_team
    task = {'language': 'python'}
    team.select_primus_by_expertise(task)
    team.select_primus_by_expertise(task)
    assert a1.has_been_primus and a2.has_been_primus
    team.select_primus_by_expertise(task)
    assert team.get_primus() is a1
    assert a1.has_been_primus
    assert not a2.has_been_primus


def test_documentation_tasks_prioritize_best_doc_expert_succeeds(
    documentation_team):
    """Test that documentation tasks prioritize best doc expert succeeds.

ReqID: N/A"""
    team, coder, writer, doc = documentation_team
    task = {'type': 'documentation', 'description': 'Write docs'}
    team.select_primus_by_expertise(task)
    primus = team.get_primus()
    assert primus in (writer, doc)
    assert primus.has_been_primus
