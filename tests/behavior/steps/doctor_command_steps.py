"""Step definitions for doctor_command.feature."""

from pytest_bdd import scenarios, when

from .cli_commands_steps import run_command

scenarios("../features/doctor_command.feature")


@when('I run the command "devsynth check"')
def run_check_alias(monkeypatch, mock_workflow_manager, command_context):
    """Invoke the doctor command via its check alias."""
    return run_command("devsynth check", monkeypatch, mock_workflow_manager, command_context)
