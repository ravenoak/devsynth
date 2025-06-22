"""Steps for the docs fetch feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/docs_fetch.feature")


@given("the docs_fetch feature context")
def given_context():
    pass


@when("we execute the docs_fetch workflow")
def when_execute():
    pass


@then("the docs_fetch workflow completes")
def then_complete():
    pass
