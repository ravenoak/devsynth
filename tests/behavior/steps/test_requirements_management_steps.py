"""Steps for the requirements management feature."""

from pytest_bdd import scenarios, given, when, then

# Import the CLI installation step for the feature background
from .cli_commands_steps import (  # noqa: F401
    devsynth_cli_installed,
    valid_devsynth_project,
    run_command,
    check_workflow_success,
)

scenarios("../features/general/requirements_management.feature")


@given("the requirements_management feature context")
def given_context():
    pass


@when("we execute the requirements_management workflow")
def when_execute():
    pass


@then("the requirements_management workflow completes")
def then_complete():
    pass
