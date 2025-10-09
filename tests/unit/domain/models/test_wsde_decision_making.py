from types import SimpleNamespace

import pytest

from devsynth.domain.models.wsde_decision_making import (
    _calculate_idea_similarity,
    evaluate_options,
)


@pytest.mark.fast
def test_calculate_idea_similarity_overlap():
    """ReqID: WSDE-DECISION-01 — computes similarity via word overlap."""
    idea1 = {"description": "fast secure api", "rationale": ""}
    idea2 = {"description": "secure api", "rationale": ""}
    sim = _calculate_idea_similarity(SimpleNamespace(), idea1, idea2)
    assert sim == pytest.approx(2 / 3)


@pytest.mark.fast
def test_evaluate_options_ranks_by_weighted_score():
    """ReqID: WSDE-DECISION-02 — ranks ideas using weighted scores."""
    ideas = [{"id": "i1"}, {"id": "i2"}]
    matrix = {
        "i1": {"crit1": 1.0, "crit2": 0.5},
        "i2": {"crit1": 0.5, "crit2": 1.0},
    }
    weights = {"crit1": 0.7, "crit2": 0.3}
    result = evaluate_options(SimpleNamespace(), ideas, matrix, weights)
    assert result[0]["id"] == "i1"
    assert result[1]["id"] == "i2"
    assert result[0]["weighted_score"] > result[1]["weighted_score"]


@pytest.mark.fast
def test_generate_diverse_ideas_filters_similar_entries(
    wsde_team_factory, stub_agent_factory
):
    """ReqID: WSDE-DECISION-05 — respects diversity threshold for idea pool."""

    agent_primary = stub_agent_factory(
        "primary",
        expertise=["security"],
        idea_batches=[
            [
                {
                    "description": "Implement encryption gateways",
                    "rationale": "Protect credentials in transit",
                }
            ]
        ],
    )
    agent_support = stub_agent_factory(
        "support",
        expertise=["generalist"],
        idea_batches=[
            [
                {
                    "description": "Implement encryption gateways",
                    "rationale": "Match partner requirements",
                },
                {
                    "description": "Adopt asynchronous audit pipeline",
                    "rationale": "Increase throughput with decoupled reviews",
                },
            ]
        ],
    )

    team = wsde_team_factory(agents=[agent_primary, agent_support])

    task = {"id": "task-idea", "domain": "security"}

    diverse = team.generate_diverse_ideas(
        task,
        max_ideas=5,
        diversity_threshold=0.8,
    )

    assert len(diverse) == 2
    assert {idea["description"] for idea in diverse} == {
        "Implement encryption gateways",
        "Adopt asynchronous audit pipeline",
    }


@pytest.mark.fast
def test_generate_diverse_ideas_handles_agent_failures(
    wsde_team_factory, stub_agent_factory
):
    """ReqID: WSDE-DECISION-06 — returns empty list when agents fail."""

    failing_agent = stub_agent_factory(
        "critic",
        expertise=["security"],
        idea_batches=[
            [{"description": "Add rate limiting", "rationale": "Protect APIs"}]
        ],
        idea_error_factory=lambda: RuntimeError("agent offline"),
    )

    team = wsde_team_factory(agents=[failing_agent])

    result = team.generate_diverse_ideas(
        {"id": "task-failure", "domain": "security"},
        max_ideas=3,
        diversity_threshold=0.7,
    )

    assert result == []


@pytest.mark.fast
def test_generate_diverse_ideas_limits_count(wsde_module_team):
    """ReqID: WSDE-DECISION-07 — truncates output to requested idea count."""

    team, _ = wsde_module_team
    task = {"id": "task-limit", "domain": "security"}

    diverse = team.generate_diverse_ideas(task, max_ideas=2, diversity_threshold=0.2)

    assert len(diverse) == 2
    descriptions = {idea["description"] for idea in diverse}
    assert "Add secure caching layer" in descriptions


@pytest.mark.fast
def test_generate_diverse_ideas_filters_duplicates_with_strict_threshold(
    wsde_module_team,
):
    """ReqID: WSDE-DECISION-08 — removes near-identical ideas when threshold is strict."""

    team, _ = wsde_module_team
    task = {"id": "task-duplicates", "domain": "security"}

    diverse = team.generate_diverse_ideas(task, max_ideas=5, diversity_threshold=0.9)

    descriptions = {idea["description"] for idea in diverse}
    assert "Add secure caching layer" in descriptions
    assert "Introduce continuous auditing" in descriptions
    assert len(descriptions) == len(diverse)
