"""Steps for the generate docs feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/generate_docs.feature")


@given("the generate_docs feature context")
def given_context():
    pass


@when("we execute the generate_docs workflow")
def when_execute():
    pass


@then("the generate_docs workflow completes")
def then_complete():
    pass
