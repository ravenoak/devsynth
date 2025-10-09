from io import StringIO
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.cli import cli_commands
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "spec_command.feature"))


@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_project_dir):
    return tmp_project_dir


@when(parsers.parse('I run the command "{command}"'))
def run_spec_command(command, monkeypatch, command_context, tmp_project_dir):
    """Execute the spec command with a mocked environment."""
    req_file = command.split()[-1]
    monkeypatch.setattr(cli_commands, "_check_services", lambda bridge: True)
    monkeypatch.setattr(cli_commands, "_validate_file_path", lambda p: None)
    monkeypatch.setattr(
        cli_commands,
        "generate_specs",
        lambda **_k: {"success": True, "output_file": "specs.md"},
    )

    captured = StringIO()
    bridge = MagicMock()
    bridge.display_result.side_effect = lambda msg: captured.write(msg + "\n")

    cli_commands.spec_cmd(requirements_file=req_file, bridge=bridge)

    command_context["output"] = captured.getvalue()
    command_context["requirements_file"] = req_file


@then(parsers.parse('the spec command should process "{req_file}"'))
def check_spec_processed(command_context, req_file):
    assert command_context["requirements_file"] == req_file


@then("generate specifications based on the requirements")
def check_generation(command_context):
    assert "Specifications generated" in command_context["output"]


@then("the workflow should execute successfully")
def workflow_success(command_context):
    assert "Specifications generated" in command_context["output"]


@then("the system should display a success message")
def success_message(command_context):
    assert "generated" in command_context["output"].lower()
