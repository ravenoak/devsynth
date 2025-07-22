"""Steps for the project ingestion feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/general/project_ingestion.feature")


@given("the project_ingestion feature context")
def given_context():
    pass


@when("we execute the project_ingestion workflow")
def when_execute():
    pass


@then("the project_ingestion workflow completes")
def then_complete():
    pass
