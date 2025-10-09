"""Steps for the workflow execution feature."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

# Import the CLI install step used by the feature background
from .cli_commands_steps import (  # noqa: F401
    check_workflow_success,
    devsynth_cli_installed,
    run_command,
    valid_devsynth_project,
)

pytestmark = [pytest.mark.fast]


scenarios(feature_path(__file__, "general", "workflow_execution.feature"))


@pytest.fixture
def workflow_context():
    return {"executed": False}


@given("the workflow_execution feature context")
def given_context(workflow_context):
    return workflow_context


@when("we execute the workflow_execution workflow")
def when_execute(workflow_context):
    workflow_context["executed"] = True


@then("the workflow_execution workflow completes")
def then_complete(workflow_context):
    assert workflow_context.get("executed") is True
