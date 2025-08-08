import types

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam


class DummyAgent:
    def __init__(self, name, expertise):
        self.name = name
        self.expertise = expertise
        self.current_role = None
        self.has_been_primus = False
        self.process = lambda task: {"solution": f"{name} solution"}


def test_assign_roles_sets_roles():
    team = WSDETeam(name="t")
    agents = [DummyAgent(f"a{i}", ["skill"]) for i in range(5)]
    team.add_agents(agents)
    team.assign_roles()
    assert team.get_primus() in agents
    roles = {a.current_role for a in agents}
    assert {"Primus", "Worker", "Supervisor", "Designer", "Evaluator"} <= roles


@pytest.mark.medium
def test_select_primus_by_expertise_prefers_match():
    team = WSDETeam(name="t")
    coder = DummyAgent("coder", ["python"])
    doc = DummyAgent("doc", ["docs"])
    team.add_agents([coder, doc])
    team.select_primus_by_expertise({"description": "Write docs"})
    assert team.get_primus() is doc


@pytest.mark.medium
def test_build_consensus_produces_result():
    team = WSDETeam(name="t")
    a1 = DummyAgent("a1", ["x"])
    a2 = DummyAgent("a2", ["y"])
    team.add_agents([a1, a2])
    task = {"id": "t1", "options": ["x", "y"]}
    team.solutions = {"t1": []}
    team.add_solution(task, {"agent": "a1", "content": "x"})
    team.add_solution(task, {"agent": "a2", "content": "y"})
    result = team.build_consensus(task)
    assert result.get("consensus")
    assert set(result.get("contributors", [])) == {"a1", "a2"}
