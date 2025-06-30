"""Steps for the code command feature."""

from io import StringIO
from unittest.mock import patch

from pytest_bdd import scenarios, when, then

scenarios("../features/code_command.feature")


@when('I run the command "devsynth code"')
def run_code_command(command_context):
    """Invoke the code command."""
    from devsynth.application.cli.cli_commands import code_cmd

    captured_output = StringIO()
    with patch("sys.stdout", new=captured_output):
        code_cmd()

    command_context["output"] = captured_output.getvalue()


@then("the code command should be executed")
def check_code_called(mock_workflow_manager):
    """Verify the workflow manager executed the code command."""
    mock_workflow_manager.execute_command.assert_any_call("code", {})
