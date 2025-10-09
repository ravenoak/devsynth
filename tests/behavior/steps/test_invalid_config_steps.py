from unittest.mock import patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]


@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_path):
    return tmp_path


scenarios(feature_path(__file__, "general", "invalid_config.feature"))


@given("the command context", target_fixture="command_context")
def command_context_fixture():
    return {}


@when(parsers.parse('I run the command "{cmd}"'))
def run_bad_command(cmd, monkeypatch, command_context):
    runner = CliRunner()
    with patch(
        "devsynth.application.cli.cli_commands.workflows.execute_command",
        return_value={"success": False, "message": "invalid key"},
    ):
        result = runner.invoke(build_app(), cmd.split()[1:])
    command_context["result"] = result


@then("the command should fail")
def command_should_fail(command_context):
    assert "invalid" in command_context["result"].output.lower()


@then(parsers.parse('the output should contain "{text}"'))
def output_should_contain(command_context, text):
    assert text.lower() in command_context["result"].output.lower()
