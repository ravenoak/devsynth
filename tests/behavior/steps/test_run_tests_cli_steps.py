"""Step definitions for run-tests CLI behavior tests."""

from pytest_bdd import then


@then("the command should exit successfully")
def command_exits_successfully(command_context):
    """Verify that the command exited with a zero status code."""
    assert command_context.get("exit_code", 1) == 0
