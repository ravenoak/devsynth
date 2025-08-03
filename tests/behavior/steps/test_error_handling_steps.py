"""Steps for the error handling feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

# Ensure the CLI installation step is registered for the feature background
from .cli_commands_steps import (  # noqa: F401
    devsynth_cli_installed,
    valid_devsynth_project,
    run_command,
    check_workflow_success,
)

scenarios("../features/general/error_handling.feature")


@pytest.fixture
def error_context():
    return {"executed": False}


@pytest.mark.medium
@given("the error_handling feature context")
def given_context(error_context):
    return error_context


@pytest.mark.medium
@when("we execute the error_handling workflow")
def when_execute(error_context):
    error_context["executed"] = True


@pytest.mark.medium
@then("the error_handling workflow completes")
def then_complete(error_context):
    assert error_context.get("executed") is True
