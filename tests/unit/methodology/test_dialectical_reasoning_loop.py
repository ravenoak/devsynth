import logging
from unittest.mock import MagicMock

from devsynth.exceptions import ConsensusError
from devsynth.methodology.dialectical_reasoning import reasoning_loop


class DummyConsensusError(ConsensusError):
    def __init__(self, message: str):  # pragma: no cover - simple helper
        Exception.__init__(self, message)


def test_reasoning_loop_runs_until_complete(monkeypatch):
    calls = []

    def fake_apply(team, task, critic, memory):
        calls.append(task.get("solution"))
        if len(calls) == 1:
            return {"status": "in_progress", "synthesis": "next"}
        return {"status": "completed", "synthesis": "final"}

    monkeypatch.setattr(
        "devsynth.methodology.dialectical_reasoning._apply_dialectical_reasoning",
        fake_apply,
    )

    results = reasoning_loop(MagicMock(), {"solution": "initial"}, MagicMock())
    assert len(results) == 2
    assert results[-1]["synthesis"] == "final"


def test_reasoning_loop_logs_consensus_failure(monkeypatch, caplog):
    def fail_apply(team, task, critic, memory):
        raise DummyConsensusError("no consensus")

    monkeypatch.setattr(
        "devsynth.methodology.dialectical_reasoning._apply_dialectical_reasoning",
        fail_apply,
    )

    with caplog.at_level(logging.ERROR):
        assert reasoning_loop(MagicMock(), {"solution": "initial"}, MagicMock()) == []
    assert "Consensus failure" in caplog.text
