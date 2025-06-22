"""Steps for the apispec generation feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/apispec_generation.feature")


@given("the apispec_generation feature context")
def given_context():
    pass


@when("we execute the apispec_generation workflow")
def when_execute():
    pass


@then("the apispec_generation workflow completes")
def then_complete():
    pass
