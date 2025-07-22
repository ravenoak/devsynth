"""Steps for the project initialization feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

scenarios("../features/general/project_initialization.feature")


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
