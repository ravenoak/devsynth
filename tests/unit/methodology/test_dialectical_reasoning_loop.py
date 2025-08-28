import importlib
import logging
from unittest.mock import MagicMock

import pytest

rl = importlib.import_module("devsynth.methodology.edrr.reasoning_loop")
from devsynth.exceptions import ConsensusError
from devsynth.methodology.edrr import reasoning_loop


class DummyConsensusError(ConsensusError):
    def __init__(self, message: str):  # pragma: no cover - simple helper
        Exception.__init__(self, message)


@pytest.mark.fast
def test_reasoning_loop_runs_until_complete(monkeypatch):
    """It continues until the reasoning process is complete.

    ReqID: DR-4
    """

    calls = []

    def fake_apply(team, task, critic, memory):
        calls.append(task.get("solution"))
        if len(calls) == 1:
            return {"status": "in_progress", "synthesis": "next"}
        return {"status": "completed", "synthesis": "final"}

    monkeypatch.setattr(rl, "_apply_dialectical_reasoning", fake_apply)

    results = reasoning_loop(MagicMock(), {"solution": "initial"}, MagicMock())
    assert len(results) == 2
    assert results[-1]["synthesis"] == "final"


@pytest.mark.fast
def test_reasoning_loop_logs_consensus_failure(monkeypatch, caplog):
    """It logs and swallows consensus failures.

    ReqID: DR-5
    """

    def fail_apply(team, task, critic, memory):
        raise DummyConsensusError("no consensus")

    monkeypatch.setattr(rl, "_apply_dialectical_reasoning", fail_apply)

    with caplog.at_level(logging.ERROR):
        assert reasoning_loop(MagicMock(), {"solution": "initial"}, MagicMock()) == []
    assert "Consensus failure" in caplog.text
    # ``log_consensus_failure`` should include the error type in the log record.
    assert caplog.records[0].error_type == "DummyConsensusError"


@pytest.mark.fast
def test_reasoning_loop_respects_max_iterations(monkeypatch):
    """It stops after reaching the iteration limit.

    ReqID: DR-6
    """

    calls = []

    def fake_apply(team, task, critic, memory):
        calls.append(1)
        return {"status": "in_progress"}

    monkeypatch.setattr(rl, "_apply_dialectical_reasoning", fake_apply)

    results = reasoning_loop(
        MagicMock(), {"solution": "initial"}, MagicMock(), max_iterations=2
    )
    assert len(results) == 2
    assert len(calls) == 2
