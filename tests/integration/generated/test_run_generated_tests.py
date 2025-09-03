"""Integration tests for running generated test suites."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from devsynth.application.agents.test import TestAgent
from devsynth.exceptions import DevSynthError


@pytest.mark.fast
def test_run_generated_tests_success(monkeypatch, tmp_path: Path) -> None:
    """run_generated_tests returns output when tests succeed."""

    agent = TestAgent()

    def fake_run(cmd, capture_output=None, text=None, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="1 passed", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    output = agent.run_generated_tests(tmp_path)

    assert "1 passed" in output


@pytest.mark.fast
def test_run_generated_tests_failure(monkeypatch, tmp_path: Path) -> None:
    """run_generated_tests raises DevSynthError on failures."""

    agent = TestAgent()

    def fake_run(cmd, capture_output=None, text=None, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="1 failed", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(DevSynthError) as excinfo:
        agent.run_generated_tests(tmp_path)

    assert "1 failed" in str(excinfo.value)
