"""Steps for the project initialization feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/project_initialization.feature")


@given("the project_initialization feature context")
def given_context():
    pass


@when("we execute the project_initialization workflow")
def when_execute():
    pass


@then("the project_initialization workflow completes")
def then_complete():
    pass
