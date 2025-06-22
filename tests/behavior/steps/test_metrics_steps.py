"""Steps for the test metrics feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/test_metrics.feature")


@given("the test_metrics feature context")
def given_context():
    pass


@when("we execute the test_metrics workflow")
def when_execute():
    pass


@then("the test_metrics workflow completes")
def then_complete():
    pass
