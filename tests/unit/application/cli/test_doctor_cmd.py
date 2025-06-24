from unittest.mock import patch

import pytest

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "doctor_cmd",
    Path(__file__).parents[4]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "commands"
    / "doctor_cmd.py",
)
doctor_cmd = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(doctor_cmd)  # type: ignore


def test_python_version_warning():
    with (
        patch.object(doctor_cmd.UnifiedConfigLoader, "load"),
        patch.object(doctor_cmd.sys, "version_info", (3, 10, 0)),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd("config")
        assert any(
            "Python 3.11 or higher" in str(call.args[0])
            for call in mock_print.call_args_list
        )


def test_missing_api_keys_warning(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with (
        patch.object(doctor_cmd.UnifiedConfigLoader, "load"),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd("config")
        output = "".join(str(c.args[0]) for c in mock_print.call_args_list)
        assert "OPENAI_API_KEY" in output and "ANTHROPIC_API_KEY" in output
