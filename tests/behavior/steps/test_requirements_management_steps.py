"""Steps for the requirements management feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/requirements_management.feature")


@given("the requirements_management feature context")
def given_context():
    pass


@when("we execute the requirements_management workflow")
def when_execute():
    pass


@then("the requirements_management workflow completes")
def then_complete():
    pass
