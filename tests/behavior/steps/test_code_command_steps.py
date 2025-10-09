from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.cli import cli_commands
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]


@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_project_dir):
    return tmp_project_dir


scenarios(feature_path(__file__, "general", "code_command.feature"))


@when('I run the command "devsynth code"')
def run_code_command(monkeypatch, command_context, tmp_project_dir):
    """Execute the code command with a mocked environment."""
    monkeypatch.setattr(cli_commands, "_check_services", lambda bridge: True)
    monkeypatch.setattr(
        cli_commands, "generate_code", lambda: {"success": True, "output_dir": "src"}
    )
    monkeypatch.setattr(cli_commands, "test_cmd", MagicMock())

    tests_dir = Path(tmp_project_dir) / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_sample.py").write_text("def test_sample():\n    assert True\n")

    captured = StringIO()
    bridge = MagicMock()
    bridge.display_result.side_effect = lambda msg: captured.write(msg + "\n")

    cli_commands.code_cmd(bridge=bridge)

    command_context["output"] = captured.getvalue()


@then("the code command should be executed")
def code_executed(command_context):
    assert "Code generated" in command_context["output"]


@then("the workflow should execute successfully")
def workflow_success(command_context):
    assert "Code generated" in command_context["output"]


@then("the system should display a success message")
def success_message(command_context):
    assert "generated" in command_context["output"].lower()
