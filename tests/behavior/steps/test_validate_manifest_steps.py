"""Steps for the validate manifest feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/validate_manifest.feature")


@given("the validate_manifest feature context")
def given_context():
    pass


@when("we execute the validate_manifest workflow")
def when_execute():
    pass


@then("the validate_manifest workflow completes")
def then_complete():
    pass
