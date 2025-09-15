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
