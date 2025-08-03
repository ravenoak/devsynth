from pytest_bdd import scenarios, when, then, given, parsers
from typer.testing import CliRunner
from unittest.mock import patch
from devsynth.adapters.cli.typer_adapter import build_app
import pytest

@pytest.mark.medium
@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    return True

@pytest.mark.medium
@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_path):
    return tmp_path

scenarios("../features/general/invalid_config.feature")

@pytest.mark.medium
@given("the command context", target_fixture="command_context")
def command_context_fixture():
    return {}

@pytest.mark.medium
@when(parsers.parse('I run the command "{cmd}"'))
def run_bad_command(cmd, monkeypatch, command_context):
    runner = CliRunner()
    with patch("devsynth.application.cli.cli_commands.workflows.execute_command", return_value={"success": False, "message": "invalid key"}):
        result = runner.invoke(build_app(), cmd.split()[1:])
    command_context["result"] = result

@pytest.mark.medium
@then("the command should fail")
def command_should_fail(command_context):
    assert "invalid" in command_context["result"].output.lower()

@pytest.mark.medium
@then(parsers.parse('the output should contain "{text}"'))
def output_should_contain(command_context, text):
    assert text.lower() in command_context["result"].output.lower()
