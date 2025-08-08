from unittest.mock import MagicMock

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


def _agent(name: str, expertise: list[str], used: bool = False):
    agent = MagicMock()
    agent.name = name
    agent.expertise = expertise
    agent.current_role = None
    agent.has_been_primus = used
    return agent


def test_initial_selection_prefers_unused_agent_succeeds():
    """Test that initial selection prefers unused agent succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdePhaseRoleRotationTeam")
    experienced = _agent("experienced", ["python"], used=True)
    newbie = _agent("newbie", [])
    team.add_agents([experienced, newbie])
    team.select_primus_by_expertise({"language": "python"})
    assert team.get_primus() is newbie
    assert newbie.has_been_primus


def test_documentation_tasks_pick_documentation_experts_succeeds():
    """Test that documentation tasks pick documentation experts succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdePhaseRoleRotationTeam")
    coder = _agent("coder", ["python"])
    doc = _agent("doc", ["documentation", "markdown"])
    team.add_agents([coder, doc])
    team.select_primus_by_expertise({"type": "documentation"})
    assert team.get_primus() is doc
    assert doc.has_been_primus


def test_assign_roles_for_phase_rotates_after_all_primus_succeeds():
    """Test that assign roles for phase rotates after all primus succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdePhaseRoleRotationTeam")
    a1 = _agent("a1", ["skill"])
    a2 = _agent("a2", ["skill"])
    team.add_agents([a1, a2])
    team.assign_roles_for_phase(Phase.EXPAND, {})
    first = team.get_primus()
    team.assign_roles_for_phase(Phase.EXPAND, {})
    second = team.get_primus()
    assert {first, second} == {a1, a2}
    assert a1.has_been_primus and a2.has_been_primus
    team.assign_roles_for_phase(Phase.EXPAND, {})
    third = team.get_primus()
    assert third is first
    assert third.has_been_primus
    other = a2 if third is a1 else a1
    assert not other.has_been_primus
