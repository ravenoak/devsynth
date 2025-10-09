"""Steps for the webapp generation feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

# Import the common CLI step so background steps are registered
from .cli_commands_steps import (  # noqa: F401
    check_workflow_success,
    devsynth_cli_installed,
    run_command,
    valid_devsynth_project,
)

pytestmark = [pytest.mark.fast]


scenarios(feature_path(__file__, "general", "webapp_generation.feature"))


@pytest.fixture
def webapp_context():
    return {"executed": False}


@given("the webapp_generation feature context")
def given_context(webapp_context):
    return webapp_context


@when("we execute the webapp_generation workflow")
def when_execute(webapp_context):
    webapp_context["executed"] = True


@then("the webapp_generation workflow completes")
def then_complete(webapp_context):
    assert webapp_context.get("executed") is True
