import subprocess

import pytest

from devsynth.application.cli.commands.mvu_exec_cmd import mvu_exec_cmd
from devsynth.interface.cli import CLIUXBridge

pytestmark = pytest.mark.fast


def test_mvu_exec_cmd_combines_streams(monkeypatch):
    """Stdout and stderr should be combined and returned."""

    def fake_run(cmd, capture_output, text):
        class Result:
            returncode = 0
            stdout = "out"
            stderr = "err"

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    bridge = CLIUXBridge()
    printed = []
    monkeypatch.setattr(bridge, "print", lambda msg: printed.append(msg))

    code = mvu_exec_cmd(["cmd"], bridge=bridge)
    assert code == 0
    assert "out" in printed[0] and "err" in printed[0]


def test_mvu_exec_cmd_returns_exit_code(monkeypatch):
    """Return code should propagate from the underlying command."""

    def fake_run(cmd, capture_output, text):
        class Result:
            returncode = 2
            stdout = ""
            stderr = "boom"

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    bridge = CLIUXBridge()
    printed = []
    monkeypatch.setattr(bridge, "print", lambda msg: printed.append(msg))

    code = mvu_exec_cmd(["cmd"], bridge=bridge)
    assert code == 2
    assert "boom" in printed[0]
