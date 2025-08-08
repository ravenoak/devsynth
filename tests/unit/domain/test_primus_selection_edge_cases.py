import inspect
from unittest.mock import MagicMock

import coverage
import pytest

from devsynth.domain.models.wsde_facade import WSDETeam


def _agent(name: str, expertise=None, used: bool = False):
    agent = MagicMock()
    agent.name = name
    if expertise is not None:
        agent.expertise = expertise
    agent.current_role = None
    agent.has_been_primus = used
    return agent


@pytest.mark.medium
def test_rotation_without_expertise_is_deterministic_succeeds():
    """Test that rotation without expertise is deterministic succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestPrimusSelectionEdgeCasesTeam")
    a1 = _agent("a1", [])
    a2 = _agent("a2", [])
    team.add_agents([a1, a2])
    team.select_primus_by_expertise({})
    assert team.get_primus() is a1
    team.select_primus_by_expertise({})
    assert team.get_primus() is a2


@pytest.mark.medium
def test_documentation_task_prefers_doc_agents_succeeds():
    """Test that documentation task prefers doc agents succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestPrimusSelectionEdgeCasesTeam")
    coder = _agent("coder", ["python"])
    writer = _agent("writer", ["documentation"])
    doc = _agent("doc", ["documentation", "markdown"])
    team.add_agents([coder, writer, doc])
    team.select_primus_by_expertise({"type": "documentation"})
    primus = team.get_primus()
    assert primus in (writer, doc)
    assert primus is not coder


@pytest.mark.medium
def test_has_been_primus_resets_after_full_rotation_succeeds():
    """Test that has been primus resets after full rotation succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestPrimusSelectionEdgeCasesTeam")
    a1 = _agent("a1", [])
    a2 = _agent("a2", [])
    team.add_agents([a1, a2])
    team.select_primus_by_expertise({})
    team.select_primus_by_expertise({})
    assert a1.has_been_primus and a2.has_been_primus
    team.select_primus_by_expertise({})
    assert team.get_primus() is a1
    assert a1.has_been_primus
    assert not a2.has_been_primus


@pytest.mark.medium
def test_edge_case_coverage_succeeds():
    """Test that edge case coverage succeeds.

    ReqID: N/A"""
    import devsynth.domain.models.wsde_facade as wsde

    cov = coverage.Coverage()
    cov.start()
    empty = wsde.WSDETeam(name="TestPrimusSelectionEdgeCasesTeam")
    empty.select_primus_by_expertise({})
    team = wsde.WSDETeam(name="TestPrimusSelectionEdgeCasesTeam")
    team.add_agents(
        [_agent("a"), _agent("b", ["documentation"]), _agent("c", ["python"])]
    )
    team.select_primus_by_expertise({"type": "documentation", "extra": {"n": 1}})
    team.select_primus_by_expertise({"language": "python"})
    team.select_primus_by_expertise({})
    team.select_primus_by_expertise({"type": "documentation"})
    team.select_primus_by_expertise({"context": {"info": [{"language": "python"}]}})
    cov.stop()
    path = wsde.__file__
    lines, start = inspect.getsourcelines(wsde.WSDETeam.select_primus_by_expertise)
    executable = []
    skip = False
    for i, line in enumerate(lines, start):
        stripped = line.strip()
        if stripped.startswith('"""'):
            if (
                stripped.count('"""') == 2
                and stripped.endswith('""')
                and stripped != '"""'
            ):
                continue
            skip = not skip
            continue
        if skip:
            if stripped.endswith('"""'):
                skip = False
            continue
        if stripped:
            executable.append(i)
    executed = set(cov.get_data().lines(path))
    coverage_percent = len(set(executable) & executed) / len(executable) * 100
    assert coverage_percent >= 80
