"""Tests for the methodology EDRR coordinator."""

from devsynth.methodology.edrr_coordinator import EDRRCoordinator


def test_automate_retrospective_review_summarizes_results() -> None:
    """It returns a summary with sprint number and categories."""
    coordinator = EDRRCoordinator()
    raw = {
        "positives": ["good"],
        "improvements": ["better"],
        "action_items": ["do"],
    }
    summary = coordinator.automate_retrospective_review(raw, 2)
    assert summary["positives"] == ["good"]
    assert summary["sprint"] == 2
