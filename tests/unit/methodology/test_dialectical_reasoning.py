"""Tests for the dialectical reasoning utilities."""

from devsynth.exceptions import ConsensusError
from devsynth.methodology.dialectical_reasoning import reasoning_loop
from devsynth.methodology.edrr_coordinator import EDRRCoordinator


def test_reasoning_loop_records_results(mocker) -> None:
    """It stores results through the coordinator."""

    coordinator = mocker.create_autospec(EDRRCoordinator, instance=True)
    result = {"status": "completed"}
    mocker.patch(
        "devsynth.methodology.dialectical_reasoning._apply_dialectical_reasoning",
        return_value=result,
    )

    output = reasoning_loop(None, {}, None, coordinator=coordinator)

    assert output == [result]
    coordinator.record_refine_results.assert_called_once_with(result)
    coordinator.record_consensus_failure.assert_not_called()


def test_reasoning_loop_logs_consensus_failure(mocker) -> None:
    """It delegates consensus failures to the coordinator."""

    coordinator = mocker.create_autospec(EDRRCoordinator, instance=True)

    class DummyConsensusError(ConsensusError):
        def __init__(self, message: str):
            Exception.__init__(self, message)

    mocker.patch(
        "devsynth.methodology.dialectical_reasoning._apply_dialectical_reasoning",
        side_effect=DummyConsensusError("no consensus"),
    )

    output = reasoning_loop(None, {}, None, coordinator=coordinator)

    assert output == []
    coordinator.record_consensus_failure.assert_called_once()
