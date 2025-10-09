import sys
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import webui_context

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "webui_commands.feature"))


@given("the WebUI is initialized")
def _init(webui_context):
    return webui_context


@when("I submit the specification form")
def submit_spec(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Requirements"
    webui_context["st"].form_submit_button.side_effect = [True, False]
    webui_context["ui"].run()


@when("I submit the inspect form")
def submit_inspect(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Requirements"
    webui_context["st"].form_submit_button.side_effect = [False, True]
    webui_context["ui"].run()


@when("I submit the test form")
def submit_test(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Synthesis"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["st"].button.side_effect = [False, False]
    webui_context["ui"].run()


@when("I click the generate code button")
def click_generate_code(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Synthesis"
    webui_context["st"].form_submit_button.return_value = False
    webui_context["st"].button.side_effect = [True, False]
    webui_context["ui"].run()


@when("I click the run pipeline button")
def click_run_pipeline(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Synthesis"
    webui_context["st"].form_submit_button.return_value = False
    webui_context["st"].button.side_effect = [False, True]
    webui_context["ui"].run()


@when("I view all configuration")
def view_all_config(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Config"
    webui_context["st"].form_submit_button.return_value = False
    webui_context["st"].button.return_value = True
    webui_context["ui"].run()


@when("I submit the edrr cycle form")
def submit_edrr_cycle(webui_context):
    webui_context["st"].sidebar.radio.return_value = "EDRR Cycle"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the alignment form")
def submit_alignment(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Alignment"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the analysis form")
def submit_analysis(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Analysis"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@then("the spec command should be executed")
def check_spec(webui_context):
    assert webui_context["cli"].spec_cmd.called


@then("the inspect command should be executed")
def check_inspect(webui_context):
    assert webui_context["cli"].inspect_cmd.called


@then("the test command should be executed")
def check_test(webui_context):
    assert webui_context["cli"].test_cmd.called


@then("the code command should be executed")
def check_code(webui_context):
    assert webui_context["cli"].code_cmd.called


@then("the run_pipeline command should be executed")
def check_run_pipeline(webui_context):
    assert webui_context["cli"].run_pipeline_cmd.called


@then("the edrr_cycle command should be executed")
def check_edrr_cycle(webui_context):
    assert webui_context["cli"].edrr_cycle_cmd.called


@then("the align command should be executed")
def check_align(webui_context):
    assert webui_context["cli"].align_cmd.called


@then("the inspect_code command should be executed")
def check_inspect_code(webui_context):
    assert webui_context["cli"].inspect_code_cmd.called
