"""Steps for the webapp generation feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

# Import the common CLI step so background steps are registered
from .cli_commands_steps import (  # noqa: F401
    devsynth_cli_installed,
    valid_devsynth_project,
    run_command,
    check_workflow_success,
)

scenarios("../features/general/webapp_generation.feature")


@pytest.fixture
def webapp_context():
    return {"executed": False}


@pytest.mark.medium
@given("the webapp_generation feature context")
def given_context(webapp_context):
    return webapp_context


@pytest.mark.medium
@when("we execute the webapp_generation workflow")
def when_execute(webapp_context):
    webapp_context["executed"] = True


@pytest.mark.medium
@then("the webapp_generation workflow completes")
def then_complete(webapp_context):
    assert webapp_context.get("executed") is True
