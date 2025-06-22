"""Steps for the code generation feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/code_generation.feature")


@given("the code_generation feature context")
def given_context():
    pass


@when("we execute the code_generation workflow")
def when_execute():
    pass


@then("the code_generation workflow completes")
def then_complete():
    pass
