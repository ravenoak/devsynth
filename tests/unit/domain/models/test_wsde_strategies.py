"""Integration tests for typed WSDE strategies."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import pytest

from devsynth.domain.models import wsde_multidisciplinary, wsde_roles, wsde_voting
from devsynth.domain.models.wsde_core import WSDETeam


@dataclass
class DummyAgent:
    name: str
    expertise: list[str] = field(default_factory=list)
    has_been_primus: bool = False
    current_role: str | None = None
    previous_role: str | None = None
    discipline: str | None = None


def _bind_team(team: WSDETeam) -> WSDETeam:
    """Attach strategy functions to ``team`` matching ``wsde_facade`` behaviour."""

    team.assign_roles = wsde_roles.assign_roles.__get__(team)
    team.dynamic_role_reassignment = wsde_roles.dynamic_role_reassignment.__get__(team)
    team.select_primus_by_expertise = wsde_roles.select_primus_by_expertise.__get__(
        team
    )
    team.vote_on_critical_decision = wsde_voting.vote_on_critical_decision.__get__(team)
    team.consensus_vote = wsde_voting.consensus_vote.__get__(team)
    team.build_consensus = wsde_voting.build_consensus.__get__(team)
    team.apply_multi_disciplinary_dialectical_reasoning = (
        wsde_multidisciplinary.apply_multi_disciplinary_dialectical_reasoning.__get__(
            team
        )
    )
    return team


@pytest.mark.fast
def test_weighted_voting_prefers_domain_expertise():
    team = _bind_team(
        WSDETeam(
            name="test-team",
            agents=[
                DummyAgent(name="generalist", expertise=["strategy"]),
                DummyAgent(
                    name="specialist",
                    expertise=["data privacy", "security"],
                    discipline="security",
                ),
                DummyAgent(name="observer", expertise=[]),
            ],
        )
    )

    task = {
        "id": "vote-1",
        "options": ["Adopt new security protocol", "Postpone decision"],
        "voting_method": "weighted",
        "domain": "security",
    }

    rng = random.Random(42)
    result = team.vote_on_critical_decision(task, rng=rng)

    assert result["status"] == "completed"
    assert result["result"]["winner"] == "Adopt new security protocol"
    assert result["weights"]["specialist"] > result["weights"]["generalist"]


@pytest.mark.fast
def test_role_assignment_uses_expertise_scores():
    agents = [
        DummyAgent(name="lead", expertise=["leadership", "coordination"]),
        DummyAgent(name="builder", expertise=["development", "testing"]),
        DummyAgent(name="designer", expertise=["architecture", "planning"]),
        DummyAgent(name="reviewer", expertise=["evaluation", "analysis"]),
    ]
    team = _bind_team(WSDETeam(name="roles", agents=agents))

    assignments = team.assign_roles()
    primus = assignments.as_name_mapping()["primus"]
    assert primus is not None and primus.name == "lead"
    role_map = team.get_role_map()
    assert role_map["lead"] == "Primus"
    assert set(role_map.keys()) == {agent.name for agent in agents}


@pytest.mark.fast
def test_multidisciplinary_analysis_structures_results():
    agents = [
        DummyAgent(name="UX", expertise=["design"], discipline="design"),
        DummyAgent(name="Dev", expertise=["implementation"], discipline="engineering"),
    ]
    team = _bind_team(WSDETeam(name="md", agents=agents))

    task = {
        "id": "multi-1",
        "description": "Improve onboarding flow with secure defaults",
        "solution": {"summary": "Add guided setup", "details": ["wizard", "tooltips"]},
        "requirements": ["Security review", {"description": "Accessible design"}],
        "success_metrics": ["reduced churn"],
    }
    knowledge = {
        "design": {
            "strengths_criteria": ["accessible"],
            "best_practices": ["inclusive design"],
            "discipline_specific_insights": ["Focus on user empathy"],
        },
        "engineering": {
            "strengths_criteria": ["secure"],
            "weaknesses_criteria": ["scalability"],
        },
    }

    result = team.apply_multi_disciplinary_dialectical_reasoning(
        task,
        critic_agent=DummyAgent(name="Critic", expertise=["evaluation"]),
        disciplinary_knowledge=knowledge,
        disciplinary_agents=agents,
    )

    assert result["method"] == "multi_disciplinary_dialectical_reasoning"
    assert len(result["perspectives"]) == 2
    assert result["evaluation"]["score"] > 0
    assert any(
        "inclusive design" in rec
        for rec in result["perspectives"][0]["recommendations"]
    )
