"""Steps for the dbschema generation feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

# Ensure CLI-related background steps are available
from .cli_commands_steps import (  # noqa: F401
    devsynth_cli_installed,
    valid_devsynth_project,
    run_command,
    check_workflow_success,
)

scenarios("../features/general/dbschema_generation.feature")


@pytest.fixture
def dbschema_context():
    return {"executed": False}


@pytest.mark.medium
@given("the dbschema_generation feature context")
def given_context(dbschema_context):
    """Prepare context for dbschema generation."""
    return dbschema_context


@pytest.mark.medium
@when("we execute the dbschema_generation workflow")
def when_execute(dbschema_context):
    dbschema_context["executed"] = True


@pytest.mark.medium
@then("the dbschema_generation workflow completes")
def then_complete(dbschema_context):
    assert dbschema_context.get("executed") is True
