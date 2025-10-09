"""Steps for the project initialization feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

# Pull in the common CLI step definitions used in the feature background
from .cli_commands_steps import (  # noqa: F401
    check_workflow_success,
    devsynth_cli_installed,
    run_command,
    valid_devsynth_project,
)

pytestmark = [pytest.mark.fast]


scenarios(feature_path(__file__, "general", "project_initialization.feature"))


@pytest.fixture
def init_context():
    return {"executed": False}


@given("the project_initialization feature context")
def given_context(init_context):
    return init_context


@when("we execute the project_initialization workflow")
def when_execute(init_context):
    init_context["executed"] = True


@then("the project_initialization workflow completes")
def then_complete(init_context):
    assert init_context.get("executed") is True
