"""Tests for the methodology EDRR coordinator."""

import pytest

from devsynth.exceptions import ConsensusError
from devsynth.methodology.edrr import EDRRCoordinator

pytestmark = [pytest.mark.fast]


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


def test_record_consensus_failure_logs(mocker) -> None:
    """It delegates consensus failures to the logger."""
    coordinator = EDRRCoordinator()
    error = ConsensusError("no consensus")
    spy = mocker.patch("devsynth.methodology.edrr.coordinator.log_consensus_failure")
    coordinator.record_consensus_failure(error)
    spy.assert_called_once()
