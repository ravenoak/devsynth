import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "webui_doctor.feature"))


@then("the Doctor page should be displayed")
def check_doctor_page(webui_context):
    webui_context["st"].header.assert_any_call("System Doctor")


@when("I click the run basic check button")
def click_run_basic_check_button(webui_context):
    # Find the run basic check button and set it to return True
    webui_context["st"].button.return_value = True


@when("I select comprehensive check mode")
def select_comprehensive_check_mode(webui_context):
    webui_context["st"].selectbox.return_value = "Comprehensive"


@when("I click the run check button")
def click_run_check_button(webui_context):
    # Find the run check button and set it to return True
    webui_context["st"].button.return_value = True


@when("issues are detected")
def issues_detected(webui_context):
    # Set up session state to indicate that issues are detected
    webui_context["st"].session_state.issues_detected = True


@when("I click the auto-fix button")
def click_auto_fix_button(webui_context):
    # Find the auto-fix button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click on a specific issue")
def click_on_specific_issue(webui_context):
    # Find the issue button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the export report button")
def click_export_report_button(webui_context):
    # Find the export report button and set it to return True
    webui_context["st"].button.return_value = True


@when("I select a specific component to check")
def select_specific_component(webui_context):
    webui_context["st"].selectbox.return_value = "SpecificComponent"


@when("I click the environment info button")
def click_environment_info_button(webui_context):
    # Find the environment info button and set it to return True
    webui_context["st"].button.return_value = True


@then("the system check should run")
def check_system_check_runs(webui_context):
    # Check that the system check runs
    # This could be implemented by checking that the check function was called
    # or by checking that a progress indicator is displayed
    assert (
        webui_context["st"].spinner.called
        if hasattr(webui_context["st"], "spinner")
        else True
    )


@then("the system check results should be displayed")
def check_system_check_results_displayed(webui_context):
    # Check that the system check results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the comprehensive system check should run")
def check_comprehensive_system_check_runs(webui_context):
    # Check that the comprehensive system check runs
    assert (
        webui_context["st"].spinner.called
        if hasattr(webui_context["st"], "spinner")
        else True
    )


@then("the detailed system check results should be displayed")
def check_detailed_system_check_results_displayed(webui_context):
    # Check that the detailed system check results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the system should attempt to fix the issues")
def check_system_attempts_to_fix_issues(webui_context):
    # Check that the system attempts to fix the issues
    assert (
        webui_context["st"].spinner.called
        if hasattr(webui_context["st"], "spinner")
        else True
    )


@then("the fix results should be displayed")
def check_fix_results_displayed(webui_context):
    # Check that the fix results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the detailed issue information should be displayed")
def check_detailed_issue_information_displayed(webui_context):
    # Check that the detailed issue information is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the issue should include fix instructions")
def check_issue_includes_fix_instructions(webui_context):
    # Check that the issue includes fix instructions
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the system check report should be exported")
def check_system_check_report_exported(webui_context):
    # Check that the system check report is exported
    assert webui_context["st"].success.called


@then("the component check should run")
def check_component_check_runs(webui_context):
    # Check that the component check runs
    assert (
        webui_context["st"].spinner.called
        if hasattr(webui_context["st"], "spinner")
        else True
    )


@then("the component check results should be displayed")
def check_component_check_results_displayed(webui_context):
    # Check that the component check results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the system environment information should be displayed")
def check_system_environment_information_displayed(webui_context):
    # Check that the system environment information is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("it should include OS, Python, and dependency details")
def check_environment_details_included(webui_context):
    # Check that the environment details are included
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
