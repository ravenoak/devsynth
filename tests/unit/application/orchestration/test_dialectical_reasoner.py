from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.collaboration.exceptions import ConsensusError
from devsynth.application.orchestration.dialectical_reasoner import DialecticalReasoner
from devsynth.application.orchestration.edrr_coordinator import EDRRCoordinator
from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.methodology.base import Phase
from devsynth.methodology.edrr import EDRRCoordinator as MethodologyEDRRCoordinator

pytestmark = [pytest.mark.fast]


class DummyConsensusError(ConsensusError):
    def __init__(self, message: str):  # pragma: no cover - simple helper
        Exception.__init__(self, message)


def test_edrr_coordinator_delegates_to_helper():
    team = MagicMock()
    coordinator = EDRRCoordinator(team)
    task = {"solution": {}}
    critic = MagicMock()
    payload = {
        "id": "step",
        "task_id": "task",
        "timestamp": datetime.now(),
        "thesis": {},
        "antithesis": {"agent": "critic", "critiques": []},
        "synthesis": {},
        "method": "dialectical_reasoning",
    }
    with patch(
        "devsynth.application.orchestration.edrr_coordinator.reasoning_loop",
        return_value=[payload],
    ) as helper:
        result = coordinator.apply_dialectical_reasoning(task, critic)
    helper.assert_called_once()
    args, kwargs = helper.call_args
    assert args[:4] == (team, task, critic, None)
    assert kwargs["phase"] == Phase.REFINE
    assert isinstance(kwargs["coordinator"], MethodologyEDRRCoordinator)
    assert isinstance(result, DialecticalSequence)
    assert result["method"] == "dialectical_reasoning"


def test_dialectical_reasoner_returns_result():
    coordinator = MagicMock()
    coordinator.apply_dialectical_reasoning.return_value = DialecticalSequence.failed(
        reason="done"
    )
    reasoner = DialecticalReasoner(coordinator)
    task = {"solution": {}}
    critic = MagicMock()
    assert isinstance(reasoner.run(task, critic), DialecticalSequence)
    coordinator.apply_dialectical_reasoning.assert_called_once_with(task, critic, None)


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
