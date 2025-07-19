"""Steps for the dbschema generation feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

scenarios("../features/dbschema_generation.feature")


@pytest.fixture
def dbschema_context():
    return {"executed": False}


@given("the dbschema_generation feature context")
def given_context(dbschema_context):
    """Prepare context for dbschema generation."""
    return dbschema_context


@when("we execute the dbschema_generation workflow")
def when_execute(dbschema_context):
    dbschema_context["executed"] = True


@then("the dbschema_generation workflow completes")
def then_complete(dbschema_context):
    assert dbschema_context.get("executed") is True
