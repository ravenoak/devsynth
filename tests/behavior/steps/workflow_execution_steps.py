"""Steps for the workflow execution feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/workflow_execution.feature")


@given("the workflow_execution feature context")
def given_context():
    pass


@when("we execute the workflow_execution workflow")
def when_execute():
    pass


@then("the workflow_execution workflow completes")
def then_complete():
    pass
