import types

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam


class SimpleAgent:
    def __init__(self, name, expertise):
        self.name = name
        self.expertise = expertise
        self.config = types.SimpleNamespace(parameters={"expertise": expertise})
        self.current_role = None


@pytest.mark.fast
def test_select_primus_updates_index_and_role():
    team = WSDETeam(name="facade")
    doc = SimpleAgent("doc", ["documentation"])
    coder = SimpleAgent("coder", ["python"])
    team.add_agents([doc, coder])
    team.select_primus_by_expertise({"type": "coding", "language": "python"})
    assert team.get_primus() is coder
    assert team.primus_index == 1
    assert getattr(coder, "has_been_primus", False)


@pytest.mark.fast
def test_dynamic_role_reassignment_rotates_primus():
    team = WSDETeam(name="facade")
    doc = SimpleAgent("doc", ["documentation"])
    coder = SimpleAgent("coder", ["python"])
    tester = SimpleAgent("tester", ["testing"])
    team.add_agents([doc, coder, tester])
    team.dynamic_role_reassignment({"type": "documentation"})
    first = team.get_primus()
    team.dynamic_role_reassignment({"type": "coding", "language": "python"})
    second = team.get_primus()
    assert first is doc
    assert second is coder
