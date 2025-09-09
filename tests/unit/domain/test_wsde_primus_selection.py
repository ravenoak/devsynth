from unittest.mock import MagicMock

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam


def _agent(name: str, expertise: list[str], used: bool = False):
    agent = MagicMock()
    agent.name = name
    agent.expertise = expertise
    agent.current_role = None
    agent.has_been_primus = used
    return agent


@pytest.mark.fast
def test_first_time_selection_prioritizes_unused_agents_succeeds():
    """Test that first time selection prioritizes unused agents succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdePrimusSelectionTeam")
    experienced = _agent("used", ["python"], used=True)
    newbie = _agent("new", ["python"], used=False)
    team.add_agents([experienced, newbie])
    team.select_primus_by_expertise({"language": "python"})
    assert team.get_primus() is newbie
    assert newbie.has_been_primus


@pytest.mark.fast
def test_rotation_resets_after_all_have_served_succeeds():
    """Test that rotation resets after all have served succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdePrimusSelectionTeam")
    a1 = _agent("a1", ["python"])
    a2 = _agent("a2", ["python"])
    team.add_agents([a1, a2])
    team.select_primus_by_expertise({"language": "python"})
    first = team.get_primus()
    team.select_primus_by_expertise({"language": "python"})
    second = team.get_primus()
    assert {first, second} == {a1, a2}
    assert a1.has_been_primus and a2.has_been_primus
    team.select_primus_by_expertise({"language": "python"})
    reset_primus = team.get_primus()
    assert reset_primus is first
    assert reset_primus.has_been_primus
    other = a2 if reset_primus is a1 else a1
    assert not other.has_been_primus


@pytest.mark.fast
def test_current_primus_considered_in_selection_succeeds():
    """Current primus remains candidate when reselection occurs.

    This prevents ``select_primus_by_expertise`` from skipping the
    existing primus simply because they've served once."""

    team = WSDETeam(name="PrimusReselectionTeam")
    py = _agent("py", ["python"])
    js = _agent("js", ["javascript"])
    team.add_agents([py, js])

    team.assign_roles()
    team.select_primus_by_expertise({"language": "python"})

    assert team.get_primus() is py


@pytest.mark.fast
def test_documentation_tasks_prefer_doc_experts_succeeds():
    """Test that documentation tasks prefer doc experts succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdePrimusSelectionTeam")
    coder = _agent("coder", ["python"])
    doc = _agent("doc", ["documentation", "markdown"])
    team.add_agents([coder, doc])
    task = {"type": "documentation", "description": "Write docs"}
    team.select_primus_by_expertise(task)
    assert team.get_primus() is doc
    assert doc.has_been_primus


@pytest.mark.fast
def test_nested_task_metadata_is_flattened_succeeds():
    """Test that nested task metadata is flattened succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdePrimusSelectionTeam")
    py = _agent("py", ["python"])
    doc = _agent("doc", ["documentation"])
    team.add_agents([doc, py])
    task = {"context": {"info": [{"language": "python"}]}}
    team.select_primus_by_expertise(task)
    assert team.get_primus() is py


@pytest.mark.fast
def test_rotation_when_all_agents_used_resets_flags_succeeds():
    """Test that rotation when all agents used resets flags succeeds.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdePrimusSelectionTeam")
    a1 = _agent("a1", ["python"], used=True)
    a2 = _agent("a2", ["docs"], used=True)
    team.add_agents([a1, a2])
    team.select_primus_by_expertise({"language": "python"})
    assert team.get_primus() is a1
    assert a1.has_been_primus
    assert not a2.has_been_primus


@pytest.mark.fast
def test_select_primus_by_expertise_coverage_succeeds():
    """Test that select primus by expertise coverage succeeds.

    ReqID: N/A"""
    import inspect
    import os
    from types import SimpleNamespace

    import coverage

    import devsynth.domain.models.wsde_facade as wsde

    team = wsde.WSDETeam(name="TestWsdePrimusSelectionTeam")
    cov = coverage.Coverage()
    cov.start()
    team.select_primus_by_expertise({})
    team.add_agent(
        SimpleNamespace(
            name="a1", expertise=["python"], current_role=None, has_been_primus=False
        )
    )
    team.add_agent(
        SimpleNamespace(
            name="a2",
            config=SimpleNamespace(
                parameters={"expertise": ["doc_generation", "markdown"]}
            ),
            current_role=None,
            has_been_primus=False,
        )
    )
    team.add_agent(
        SimpleNamespace(
            name="a3", expertise=["testing"], current_role=None, has_been_primus=False
        )
    )
    team.add_agent(
        SimpleNamespace(
            name="a4", expertise=["security"], current_role=None, has_been_primus=False
        )
    )
    team.add_agent(
        SimpleNamespace(
            name="a5",
            expertise=["javascript"],
            current_role=None,
            has_been_primus=False,
        )
    )
    team.add_agent(
        SimpleNamespace(
            name="a6", expertise=["api"], current_role=None, has_been_primus=False
        )
    )
    team.add_agent(
        SimpleNamespace(
            name="a7", expertise=["design"], current_role=None, has_been_primus=False
        )
    )
    team.select_primus_by_expertise(
        {"type": "documentation", "details": [1, 2], "extra": {"foo": "bar"}}
    )
    team.select_primus_by_expertise({"language": "python"})
    team.select_primus_by_expertise({"type": "testing"})
    team.select_primus_by_expertise({"type": "documentation"})
    team.select_primus_by_expertise({"type": "security"})
    team.select_primus_by_expertise({"type": "frontend"})
    team.select_primus_by_expertise({"type": "backend"})
    team.select_primus_by_expertise({"type": "design"})
    cov.stop()
    path = inspect.getsourcefile(wsde.WSDETeam.select_primus_by_expertise)
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
    assert coverage_percent >= 30
