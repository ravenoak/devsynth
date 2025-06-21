from unittest.mock import patch

import pytest

from devsynth.application.cli.commands import doctor_cmd


@patch("devsynth.application.cli.commands.doctor_cmd.load_config")
def test_python_version_warning(mock_load):
    with patch.object(doctor_cmd.sys, "version_info", (3, 10, 0)), patch.object(
        doctor_cmd.bridge, "print"
    ) as mock_print:
        doctor_cmd.doctor_cmd("config")
        assert any(
            "Python 3.11 or higher" in str(call.args[0])
            for call in mock_print.call_args_list
        )


@patch("devsynth.application.cli.commands.doctor_cmd.load_config")
def test_missing_api_keys_warning(mock_load, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with patch.object(doctor_cmd.bridge, "print") as mock_print:
        doctor_cmd.doctor_cmd("config")
        output = "".join(str(c.args[0]) for c in mock_print.call_args_list)
        assert "OPENAI_API_KEY" in output and "ANTHROPIC_API_KEY" in output

