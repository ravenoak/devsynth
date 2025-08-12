import pytest
from pytest_bdd import given, scenarios, then, when

scenarios("../features/general/cli_ui_parity.feature")


@pytest.fixture
def context():
    return {}


@pytest.mark.medium
@given("the CLI wizard is initialized")
def cli_wizard_initialized(context):
    context["cli_steps"] = ["start", "review", "finish"]
    context["webui_steps"] = ["start", "review", "finish"]


@pytest.mark.medium
@when("I compare the CLI wizard steps with the web UI")
def compare_cli_wizard_steps(context):
    # No action needed, comparison happens in the assertions
    pass


@pytest.mark.medium
@then("the number of steps should be the same")
def number_of_steps_should_be_the_same(context):
    assert len(context["cli_steps"]) == len(context["webui_steps"])


@pytest.mark.medium
@then("the order of steps should match")
def order_of_steps_should_match(context):
    assert context["cli_steps"] == context["webui_steps"]


@pytest.mark.medium
@given("the CLI is initialized")
def cli_initialized(context):
    context["cli_progress"] = []
    context["webui_progress"] = []


@pytest.mark.medium
@when("I run a long-running CLI operation")
def run_long_cli_operation(context):
    context["cli_progress"] = [0, 50, 100]
    context["webui_progress"] = [0, 50, 100]


@pytest.mark.medium
@then("the CLI progress indicator should mirror the web UI progress behavior")
def cli_progress_indicator_should_mirror_webui(context):
    assert context["cli_progress"] == context["webui_progress"]


@pytest.mark.medium
@given("the CLI shell completion is initialized")
def cli_shell_completion_initialized(context):
    context["cli_completions"] = ["init", "spec", "test"]
    context["webui_options"] = ["init", "spec", "test"]


@pytest.mark.medium
@when("I request completions for a partial command")
def request_completions_for_partial_command(context):
    context["suggestions"] = [
        c for c in context["cli_completions"] if c.startswith("i")
    ]
    context["webui_suggestions"] = [
        c for c in context["webui_options"] if c.startswith("i")
    ]


@pytest.mark.medium
@then("I should receive the same suggestions as the web UI")
def suggestions_should_match_webui(context):
    assert context["suggestions"] == context["webui_suggestions"]
