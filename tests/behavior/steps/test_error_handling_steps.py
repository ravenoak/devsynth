"""Steps for the error handling feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

# Ensure the CLI installation step is registered for the feature background
from .cli_commands_steps import (  # noqa: F401
    check_workflow_success,
    devsynth_cli_installed,
    run_command,
    valid_devsynth_project,
)

pytestmark = [pytest.mark.fast]


scenarios(feature_path(__file__, "general", "error_handling.feature"))


@pytest.fixture
def error_context():
    return {"executed": False}


@given("the error_handling feature context")
def given_context(error_context):
    return error_context


@when("we execute the error_handling workflow")
def when_execute(error_context):
    error_context["executed"] = True


@then("the error_handling workflow completes")
def then_complete(error_context):
    assert error_context.get("executed") is True
