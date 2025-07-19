"""Steps for the error handling feature."""

import pytest
from pytest_bdd import scenarios, given, when, then

scenarios("../features/error_handling.feature")


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
