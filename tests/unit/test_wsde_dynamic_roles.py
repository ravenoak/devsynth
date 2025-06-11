import pytest
from unittest.mock import MagicMock

from devsynth.domain.models.wsde import WSDETeam
from devsynth.methodology.base import Phase


class SimpleAgent:
    def __init__(self, name, expertise=None):
        self.name = name
        self.expertise = expertise or []
        self.current_role = None


def test_assign_roles_for_phase_selects_primus_by_expertise():
    team = WSDETeam()
    expand_agent = SimpleAgent("expander", ["expand"])
    diff_agent = SimpleAgent("differ", ["differentiate"])

    team.add_agents([expand_agent, diff_agent])

    task = {"description": "demo"}

    team.assign_roles_for_phase(Phase.EXPAND, task)
    assert team.get_primus() == expand_agent

    team.assign_roles_for_phase(Phase.DIFFERENTIATE, task)
    assert team.get_primus() == diff_agent
