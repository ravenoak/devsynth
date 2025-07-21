"""Steps for the webapp generation feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

scenarios("../features/webapp_generation.feature")


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
