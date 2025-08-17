from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.collaboration.exceptions import ConsensusError
from devsynth.application.orchestration.dialectical_reasoner import DialecticalReasoner
from devsynth.application.orchestration.edrr_coordinator import EDRRCoordinator
from devsynth.methodology.base import Phase
from devsynth.methodology.edrr import EDRRCoordinator as MethodologyEDRRCoordinator


class DummyConsensusError(ConsensusError):
    def __init__(self, message: str):  # pragma: no cover - simple helper
        Exception.__init__(self, message)


@pytest.mark.medium
def test_edrr_coordinator_delegates_to_helper():
    team = MagicMock()
    coordinator = EDRRCoordinator(team)
    task = {"solution": {}}
    critic = MagicMock()
    with patch(
        "devsynth.application.orchestration.edrr_coordinator.reasoning_loop",
        return_value=[{"ok": True}],
    ) as helper:
        result = coordinator.apply_dialectical_reasoning(task, critic)
    helper.assert_called_once()
    args, kwargs = helper.call_args
    assert args[:4] == (team, task, critic, None)
    assert kwargs["phase"] == Phase.REFINE
    assert isinstance(kwargs["coordinator"], MethodologyEDRRCoordinator)
    assert result == {"ok": True}


@pytest.mark.medium
def test_dialectical_reasoner_returns_result():
    coordinator = MagicMock()
    coordinator.apply_dialectical_reasoning.return_value = {"done": True}
    reasoner = DialecticalReasoner(coordinator)
    task = {"solution": {}}
    critic = MagicMock()
    assert reasoner.run(task, critic) == {"done": True}
    coordinator.apply_dialectical_reasoning.assert_called_once_with(task, critic, None)


@pytest.mark.medium
def test_dialectical_reasoner_logs_consensus_failure(caplog):
    coordinator = MagicMock()
    coordinator.apply_dialectical_reasoning.side_effect = DummyConsensusError(
        "no consensus"
    )
    reasoner = DialecticalReasoner(coordinator)
    task = {"solution": {}}
    critic = MagicMock()
    with caplog.at_level("ERROR"):
        assert reasoner.run(task, critic) is None
    assert "Consensus failure" in caplog.text
