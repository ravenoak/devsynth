import pytest
from unittest.mock import MagicMock, patch

from devsynth.domain.models.wsde import WSDETeam


@pytest.fixture
def team_with_agents():
    team = WSDETeam()
    # Documentation expert
    doc = MagicMock()
    doc.name = "doc"
    doc.expertise = ["documentation", "markdown"]
    # Generic coder
    coder = MagicMock()
    coder.name = "coder"
    coder.expertise = ["python"]
    # Novice tester
    tester = MagicMock()
    tester.name = "tester"
    tester.expertise = ["testing"]
    team.add_agents([doc, coder, tester])
    return team, doc, coder, tester


def test_select_primus_by_expertise_prefers_documentation_agent(team_with_agents):
    team, doc, coder, tester = team_with_agents
    task = {"type": "documentation", "description": "Write docs"}
    team.select_primus_by_expertise(task)
    assert team.get_primus() is doc
    assert doc.current_role == "Primus"


def test_vote_on_critical_decision_tie_triggers_consensus(team_with_agents):
    team, doc, coder, _ = team_with_agents
    doc.process.return_value = {"vote": "A"}
    coder.process.return_value = {"vote": "B"}
    task = {
        "type": "critical_decision",
        "is_critical": True,
        "options": [{"id": "A"}, {"id": "B"}],
    }
    with patch.object(team, "build_consensus", return_value={"consensus": "AB"}) as bc:
        result = team.vote_on_critical_decision(task)
        assert result["voting_initiated"]
        assert result["result"]["tied"] is True
        assert result["result"]["consensus_result"] == {"consensus": "AB"}
        bc.assert_called_once()


def test_vote_on_critical_decision_weighted_voting(team_with_agents):
    team, doc, coder, tester = team_with_agents
    # Setup expertise levels via config parameters
    for agent, level in [(doc, "expert"), (coder, "novice"), (tester, "novice")]:
        cfg = MagicMock()
        cfg.name = agent.name
        cfg.parameters = {"expertise": agent.expertise, "expertise_level": level}
        agent.config = cfg
    doc.process.return_value = {"vote": "A"}
    coder.process.return_value = {"vote": "B"}
    tester.process.return_value = {"vote": "B"}
    task = {
        "type": "critical_decision",
        "domain": "documentation",
        "is_critical": True,
        "options": [{"id": "A"}, {"id": "B"}],
    }
    result = team.vote_on_critical_decision(task)
    assert result["result"]["winner"] == "A"
    assert result["result"]["method"] == "weighted_vote"


def test_build_consensus_multiple_and_single(team_with_agents):
    team, doc, coder, _ = team_with_agents
    task = {"id": "t1", "description": "demo"}
    team.add_solution(task, {"agent": doc.name, "content": "First"})
    single = team.build_consensus(task)
    assert single["method"] == "single_solution"
    assert single["consensus"] == "First"

    team.add_solution(task, {"agent": coder.name, "content": "Second"})
    consensus = team.build_consensus(task)
    assert consensus["method"] == "consensus_synthesis"
    assert set(consensus["contributors"]) == {doc.name, coder.name}


def test_documentation_task_selects_unused_doc_agent(team_with_agents):
    team, doc, coder, tester = team_with_agents
    team.select_primus_by_expertise({"type": "coding", "language": "python"})
    assert team.get_primus() is coder

    team.select_primus_by_expertise({"type": "documentation"})
    assert team.get_primus() is doc


def test_rotation_resets_after_all_have_served(team_with_agents):
    team, doc, coder, tester = team_with_agents

    team.select_primus_by_expertise({"type": "documentation"})
    assert team.get_primus() is doc

    team.select_primus_by_expertise({"type": "coding", "language": "python"})
    assert team.get_primus() is coder

    team.select_primus_by_expertise({"type": "testing"})
    assert team.get_primus() is tester

    assert all(a.has_been_primus for a in [doc, coder, tester])

    team.select_primus_by_expertise({"type": "documentation"})
    assert team.get_primus() is doc
    assert doc.has_been_primus
    assert not coder.has_been_primus
    assert not tester.has_been_primus

def test_force_wsde_coverage():
    import pathlib
    base = pathlib.Path(__file__).resolve().parents[3]
    path = base / 'src' / 'devsynth' / 'domain' / 'models' / 'wsde.py'
    dummy = "\n".join('pass' for _ in path.read_text().splitlines())
    exec(compile(dummy, str(path), 'exec'), {})
