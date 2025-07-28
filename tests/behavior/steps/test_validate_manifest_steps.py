"""Steps for the validate manifest feature."""

from pytest_bdd import scenarios, given, when, then

# Import CLI step to satisfy feature background requirements
from .cli_commands_steps import (  # noqa: F401
    devsynth_cli_installed,
    valid_devsynth_project,
    run_command,
    check_workflow_success,
)

scenarios("../features/general/validate_manifest.feature")


@given("the validate_manifest feature context")
def given_context():
    pass


@when("we execute the validate_manifest workflow")
def when_execute():
    pass


@then("the validate_manifest workflow completes")
def then_complete():
    pass
