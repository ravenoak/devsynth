"""Steps for the retry mechanism feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/retry_mechanism.feature")


@given("the retry_mechanism feature context")
def given_context():
    pass


@when("we execute the retry_mechanism workflow")
def when_execute():
    pass


@then("the retry_mechanism workflow completes")
def then_complete():
    pass
