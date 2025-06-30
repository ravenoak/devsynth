"""Steps for the spec command feature."""

from io import StringIO
from unittest.mock import patch

from pytest_bdd import scenarios, when, then, parsers

scenarios("../features/spec_command.feature")


@when(parsers.parse('I run the command "devsynth spec --requirements-file {req_file}"'))
def run_spec_command(req_file, command_context):
    """Invoke the spec command with a requirements file."""
    from devsynth.application.cli.cli_commands import spec_cmd

    captured_output = StringIO()
    with patch("sys.stdout", new=captured_output):
        spec_cmd(requirements_file=req_file)

    command_context["output"] = captured_output.getvalue()


@then(parsers.parse('the spec command should process "{req_file}"'))
def check_spec_called(req_file, mock_workflow_manager):
    """Verify the workflow manager received the spec command."""
    mock_workflow_manager.execute_command.assert_any_call(
        "spec", {"requirements_file": req_file}
    )
