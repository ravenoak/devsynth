"""Steps for the doctor command feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/doctor_command.feature")


@given("the doctor_command feature context")
def given_context():
    pass


@when("we execute the doctor_command workflow")
def when_execute():
    pass


@then("the doctor_command workflow completes")
def then_complete():
    pass
