import pytest
from pytest_bdd import given, parsers, then, when
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app

pytestmark = [pytest.mark.medium]


@given("the DevSynth CLI is installed")
def devsynth_cli_installed() -> bool:
    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_project_dir):
    return tmp_project_dir


@when(parsers.parse('I run the command "{command}"'))
def run_exec_command(command: str, command_context):
    args = command.split()
    if args[0] == "devsynth":
        args = args[1:]
    runner = CliRunner()
    result = runner.invoke(build_app(), args)
    command_context["exit_code"] = result.exit_code
    command_context["output"] = result.output


@then("the command should succeed")
def command_should_succeed(command_context) -> None:
    assert command_context.get("exit_code") == 0


@then(parsers.parse('the output should contain "{text}"'))
def output_should_contain(text: str, command_context) -> None:
    assert text in command_context.get("output", "")
