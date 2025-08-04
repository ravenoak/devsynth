"""Tests for the run_tests_cmd CLI wrapper."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest
import typer

# Create minimal stubs to avoid importing heavy modules when loading run_tests_cmd
cli_stub = ModuleType("devsynth.interface.cli")


class _Bridge:
    def print(self, *args, **kwargs):
        pass


cli_stub.CLIUXBridge = _Bridge
sys.modules["devsynth.interface.cli"] = cli_stub

ux_stub = ModuleType("devsynth.interface.ux_bridge")
ux_stub.UXBridge = object
sys.modules["devsynth.interface.ux_bridge"] = ux_stub

logging_stub = ModuleType("devsynth.logging_setup")


class _Logger:
    def __init__(self, *args, **kwargs):
        pass


logging_stub.DevSynthLogger = _Logger
logging_stub.configure_logging = lambda *a, **k: None
sys.modules["devsynth.logging_setup"] = logging_stub

run_tests_module = ModuleType("devsynth.testing.run_tests")
run_tests_module.run_tests = lambda *a, **k: (True, "")
sys.modules["devsynth.testing.run_tests"] = run_tests_module

spec = importlib.util.spec_from_file_location(
    "run_tests_cmd",
    Path(__file__).resolve().parents[5]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "commands"
    / "run_tests_cmd.py",
)
run_tests_cmd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_tests_cmd)


class DummyBridge:
    def print(self, *args, **kwargs):  # pragma: no cover - simple stub
        pass


def test_run_tests_cmd_invokes_runner() -> None:
    """run_tests_cmd should call the underlying run_tests helper."""
    with patch.object(
        run_tests_cmd, "run_tests", return_value=(True, "ok")
    ) as mock_run:
        run_tests_cmd.run_tests_cmd(
            target="unit-tests", fast=True, bridge=DummyBridge()
        )
        mock_run.assert_called_once()


def test_run_tests_cmd_nonzero_exit() -> None:
    """run_tests_cmd exits with code 1 when tests fail."""
    with patch.object(run_tests_cmd, "run_tests", return_value=(False, "bad")):
        with pytest.raises(typer.Exit) as exc:
            run_tests_cmd.run_tests_cmd(target="unit-tests", bridge=DummyBridge())
        assert exc.value.exit_code == 1
