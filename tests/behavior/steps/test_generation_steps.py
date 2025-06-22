"""Steps for the test generation feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/test_generation.feature")


@given("the test_generation feature context")
def given_context():
    pass


@when("we execute the test_generation workflow")
def when_execute():
    pass


@then("the test_generation workflow completes")
def then_complete():
    pass
