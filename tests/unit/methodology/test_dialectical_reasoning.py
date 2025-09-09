"""Tests for the dialectical reasoning utilities."""

import pytest

from devsynth.domain.models.memory import MemoryType
from devsynth.exceptions import ConsensusError
from devsynth.methodology.base import Phase
from devsynth.methodology.edrr import EDRRCoordinator, reasoning_loop


@pytest.mark.fast
def test_reasoning_loop_records_results(mocker) -> None:
    """It stores results through the coordinator.

    ReqID: DR-1
    """

    coordinator = mocker.create_autospec(EDRRCoordinator, instance=True)
    result = {"status": "completed"}
    mocker.patch(
        "devsynth.methodology.edrr.reasoning_loop._apply_dialectical_reasoning",
        return_value=result,
    )

    output = reasoning_loop(None, {}, None, coordinator=coordinator)

    assert output == [result]
    coordinator.record_refine_results.assert_called_once_with(result)
    coordinator.record_consensus_failure.assert_not_called()


@pytest.mark.fast
def test_reasoning_loop_logs_consensus_failure(mocker) -> None:
    """It delegates consensus failures to the coordinator.

    ReqID: DR-2
    """

    coordinator = mocker.create_autospec(EDRRCoordinator, instance=True)

    class DummyConsensusError(ConsensusError):
        def __init__(self, message: str):
            Exception.__init__(self, message)

    mocker.patch(
        "devsynth.methodology.edrr.reasoning_loop._apply_dialectical_reasoning",
        side_effect=DummyConsensusError("no consensus"),
    )

    output = reasoning_loop(None, {}, None, coordinator=coordinator)

    assert output == []
    coordinator.record_consensus_failure.assert_called_once()


@pytest.mark.fast
def test_reasoning_loop_persists_phase_results(mocker) -> None:
    """It stores results using the memory manager.

    ReqID: DR-3
    """

    memory_manager = mocker.Mock()
    coordinator = EDRRCoordinator(memory_manager)
    result = {"status": "completed"}
    mocker.patch(
        "devsynth.methodology.edrr.reasoning_loop._apply_dialectical_reasoning",
        return_value=result,
    )

    reasoning_loop(None, {}, None, coordinator=coordinator, phase=Phase.DIFFERENTIATE)

    memory_manager.store_with_edrr_phase.assert_called_once_with(
        result, MemoryType.KNOWLEDGE, "DIFFERENTIATE"
    )
