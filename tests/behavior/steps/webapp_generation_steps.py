"""Steps for the webapp generation feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/webapp_generation.feature")


@given("the webapp_generation feature context")
def given_context():
    pass


@when("we execute the webapp_generation workflow")
def when_execute():
    pass


@then("the webapp_generation workflow completes")
def then_complete():
    pass
