"""Steps for the error handling feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/error_handling.feature")


@given("the error_handling feature context")
def given_context():
    pass


@when("we execute the error_handling workflow")
def when_execute():
    pass


@then("the error_handling workflow completes")
def then_complete():
    pass
