import pytest

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

"""Steps for the requirements management feature."""

from pytest_bdd import given, scenarios, then, when

# Import the CLI installation step for the feature background
from .cli_commands_steps import (  # noqa: F401
    check_workflow_success,
    devsynth_cli_installed,
    run_command,
    valid_devsynth_project,
)

scenarios(feature_path(__file__, "general", "requirements_management.feature"))


@pytest.fixture
def command_context():
    """Shared context for CLI command results."""
    return {}


@given("the requirements_management feature context")
def given_context(command_context):
    """Provide a context object for subsequent steps."""
    return command_context


@when("we execute the requirements_management workflow")
def when_execute(command_context):
    """Run a representative requirements command."""
    run_command("devsynth requirements --action list", command_context)


@then("the requirements_management workflow completes")
def then_complete(command_context):
    """Verify the command executed successfully."""
    check_workflow_success(command_context)
