"""Steps for the validate manifest command feature."""

from pytest_bdd import scenarios, then

from .cli_commands_steps import run_command  # noqa: F401

scenarios("../features/validate_manifest_command.feature")


@then("the output should indicate the project configuration is valid")
def manifest_valid(command_context):
    """Check for a success message from validate-manifest."""
    output = command_context.get("output", "")
    assert "Project configuration is valid" in output
