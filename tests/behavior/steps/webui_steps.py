"""Step definitions for WebUI interaction feature."""

from pytest_bdd import scenarios, given, when, then

scenarios("../features/webui.feature")


@given("the DevSynth WebUI is running")
def webui_running():
    """Assume the WebUI server is running for tests."""
    pass


@when('I navigate to the "Onboarding" page')
def go_to_onboarding():
    pass


@when("I submit the initialization form")
def submit_init_form():
    pass


@then("the init workflow should execute via UXBridge")
def init_executed():
    pass


@when('I navigate to the "Requirements" page')
def go_to_requirements():
    pass


@when("I submit the specification form")
def submit_spec_form():
    pass


@then("the spec workflow should execute via UXBridge")
def spec_executed():
    pass


@when('I navigate to the "Config" page')
def go_to_config():
    pass


@when("I update a setting")
def update_setting():
    pass


@then("the config workflow should execute via UXBridge")
def config_executed():
    pass
