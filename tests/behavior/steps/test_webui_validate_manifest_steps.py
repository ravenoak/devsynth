import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "validate_manifest.feature"))


@then("the validate manifest page should be displayed")
def check_validate_manifest_page(webui_context):
    webui_context["st"].header.assert_any_call("Validate Manifest")


@when("I select custom validation rules")
def select_custom_validation_rules(webui_context):
    webui_context["st"].multiselect = pytest.MagicMock(return_value=["Rule1", "Rule2"])


@when("validation issues are found")
def validation_issues_found(webui_context):
    # Mock that validation issues are found
    # This could be implemented by setting up a specific return value
    # or by modifying the session state
    webui_context["st"].session_state.validation_issues = True


@when("I click the auto-fix button")
def click_auto_fix_button(webui_context):
    # Find the auto-fix button in columns and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False


@when("I click the validation history button")
def click_validation_history_button(webui_context):
    # Find the history button in columns and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col2_mock.button.return_value = True
    col1_mock.button.return_value = False


@then("the manifest validation results should be displayed")
def check_validation_results_displayed(webui_context):
    # Check that the validation results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the manifest validation results with custom rules should be displayed")
def check_custom_validation_results_displayed(webui_context):
    # Check that the validation results with custom rules are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks based on the actual implementation


@then("the manifest issues should be fixed automatically")
def check_issues_fixed(webui_context):
    # Check that the issues are fixed
    # This could be implemented by checking that the auto-fix function was called
    # or by checking that a success message is displayed
    assert webui_context["st"].success.called


@then("a success message should be displayed")
def check_success_message(webui_context):
    # Check that a success message is displayed
    webui_context["st"].success.assert_called_once()


@then("the manifest validation report should be exported")
def check_validation_report_exported(webui_context):
    # Check that a success message is shown after export
    webui_context["st"].success.assert_called_once()


@then("the manifest validation history should be displayed")
def check_validation_history_displayed(webui_context):
    # Check that the validation history is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("previous validation results should be available for review")
def check_previous_results_available(webui_context):
    # Check that previous validation results are displayed
    # This could be implemented by checking that the history data is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
