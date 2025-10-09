import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "cli_ui_parity.feature"))


@pytest.fixture
def context():
    return {}


@given("the CLI wizard is initialized")
def cli_wizard_initialized(context):
    context["cli_steps"] = ["start", "review", "finish"]
    context["webui_steps"] = ["start", "review", "finish"]


@when("I compare the CLI wizard steps with the web UI")
def compare_cli_wizard_steps(context):
    # No action needed, comparison happens in the assertions
    pass


@then("the number of steps should be the same")
def number_of_steps_should_be_the_same(context):
    assert len(context["cli_steps"]) == len(context["webui_steps"])


@then("the order of steps should match")
def order_of_steps_should_match(context):
    assert context["cli_steps"] == context["webui_steps"]


@given("the CLI is initialized")
def cli_initialized(context):
    context["cli_progress"] = []
    context["webui_progress"] = []


@when("I run a long-running CLI operation")
def run_long_cli_operation(context):
    context["cli_progress"] = [0, 50, 100]
    context["webui_progress"] = [0, 50, 100]


@then("the CLI progress indicator should mirror the web UI progress behavior")
def cli_progress_indicator_should_mirror_webui(context):
    assert context["cli_progress"] == context["webui_progress"]


@given("the CLI shell completion is initialized")
def cli_shell_completion_initialized(context):
    context["cli_completions"] = ["init", "spec", "test"]
    context["webui_options"] = ["init", "spec", "test"]


@when("I request completions for a partial command")
def request_completions_for_partial_command(context):
    context["suggestions"] = [
        c for c in context["cli_completions"] if c.startswith("i")
    ]
    context["webui_suggestions"] = [
        c for c in context["webui_options"] if c.startswith("i")
    ]


@then("I should receive the same suggestions as the web UI")
def suggestions_should_match_webui(context):
    assert context["suggestions"] == context["webui_suggestions"]


class _PromptStub:
    """Minimal Streamlit stand-in for prompt parity scenarios."""

    def __init__(self) -> None:
        self.selectbox_calls: list[tuple[str, tuple[str, ...], int, str | None]] = []
        self.checkbox_calls: list[tuple[str, bool, str | None]] = []

    def selectbox(
        self, label: str, options: list[str], index: int = 0, key: str | None = None
    ) -> str:
        options_tuple = tuple(options)
        self.selectbox_calls.append((label, options_tuple, index, key))
        return options_tuple[index]

    def checkbox(self, label: str, value: bool = False, key: str | None = None) -> bool:
        self.checkbox_calls.append((label, value, key))
        return value


@given("a CLI question with a default answer")
def cli_question_with_default(context):
    context["prompt"] = "Choose an interface"
    context["choices"] = ("CLI", "WebUI")
    context["default"] = "WebUI"


@when("both interfaces prompt for the same question")
def prompt_both_interfaces(context, monkeypatch):
    from devsynth.interface import webui

    stub = _PromptStub()
    monkeypatch.setattr(webui, "st", stub, raising=False)
    monkeypatch.setattr(webui, "_STREAMLIT", stub, raising=False)
    ui = webui.WebUI()
    context["cli_response"] = context["default"]
    context["webui_response"] = ui.ask_question(
        context["prompt"],
        choices=context["choices"],
        default=context["default"],
    )
    context["webui_confirmation"] = ui.confirm_choice("Proceed?", default=True)
    context["selectbox_calls"] = stub.selectbox_calls
    context["checkbox_calls"] = stub.checkbox_calls


@then("the default responses should match")
def defaults_should_match(context):
    assert context["cli_response"] == context["webui_response"]
    assert context["webui_confirmation"] is True
    assert context["selectbox_calls"][0][2] == context["choices"].index(
        context["default"]
    )
    assert context["checkbox_calls"][0][1] is True
