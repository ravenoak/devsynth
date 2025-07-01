"""Steps for the doctor.feature without mocks."""

from pytest_bdd import given, scenarios, when

from .cli_commands_steps import run_command

scenarios("../features/doctor.feature")


@given("valid environment configuration")
def valid_env(tmp_path, monkeypatch):
    """Set the working directory to a valid project."""
    monkeypatch.chdir(tmp_path)


@when('I run the command "devsynth doctor"')
def run_doctor(monkeypatch, mock_workflow_manager, command_context):
    """Invoke the doctor command."""
    return run_command(
        "devsynth doctor",
        monkeypatch,
        mock_workflow_manager,
        command_context,
    )
