from pytest_bdd import given, when, then, scenarios, parsers

from .webui_steps import webui_context
import pytest

scenarios("../features/general/webui_navigation_prompts.feature")


@pytest.mark.medium
@given("the WebUI is initialized")
def init_webui(webui_context):
    return webui_context


@pytest.mark.medium
@when(parsers.parse('I navigate to "{page}"'))
def nav_to(page, webui_context):
    webui_context["st"].sidebar.radio.return_value = page
    webui_context["ui"].run()


@pytest.mark.medium
@when("I submit the onboarding form")
def submit_form(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@pytest.mark.medium
@then(parsers.parse('the "{header}" header is shown'))
def header_shown(header, webui_context):
    webui_context["st"].header.assert_any_call(header)


@pytest.mark.medium
@then("the init command should be executed")
def init_called(webui_context):
    assert webui_context["cli"].init_cmd.called
