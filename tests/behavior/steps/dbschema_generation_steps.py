"""Steps for the dbschema generation feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/dbschema_generation.feature")


@given("the dbschema_generation feature context")
def given_context():
    pass


@when("we execute the dbschema_generation workflow")
def when_execute():
    pass


@then("the dbschema_generation workflow completes")
def then_complete():
    pass
