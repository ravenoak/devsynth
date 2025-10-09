import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "refactor.feature"))


@then("the refactor page should be displayed")
def check_refactor_page(webui_context):
    webui_context["st"].header.assert_any_call("Code Refactoring")


@when("I select source code for analysis")
def select_source_code_for_analysis(webui_context):
    # Mock the file uploader or directory selector
    webui_context["st"].text_input.return_value = "/path/to/source/code"


@when("I submit the refactor analysis form")
def submit_refactor_analysis_form(webui_context):
    webui_context["st"].form_submit_button.return_value = True


@when("I select source code for refactoring")
def select_source_code_for_refactoring(webui_context):
    # Mock the file uploader or directory selector
    webui_context["st"].text_input.return_value = "/path/to/source/code"


@when("I select automatic refactoring mode")
def select_automatic_refactoring_mode(webui_context):
    webui_context["st"].selectbox.return_value = "Automatic"


@when("I select guided refactoring mode")
def select_guided_refactoring_mode(webui_context):
    webui_context["st"].selectbox.return_value = "Guided"


@when("I select specific refactoring patterns")
def select_specific_refactoring_patterns(webui_context):
    # Mock the multiselect function if it's used in the page
    webui_context["st"].multiselect = pytest.MagicMock(
        return_value=["Pattern1", "Pattern2"]
    )


@when("I submit the refactor form")
def submit_refactor_form(webui_context):
    webui_context["st"].form_submit_button.return_value = True


@when("I click the preview button")
def click_preview_button(webui_context):
    # Find the preview button and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False


@when("I click the refactoring history button")
def click_refactoring_history_button(webui_context):
    # Find the history button and set it to return True
    webui_context["st"].button.return_value = True


@then("the refactoring opportunities should be displayed")
def check_refactoring_opportunities_displayed(webui_context):
    # Check that the refactoring opportunities are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the code should be refactored automatically")
def check_code_refactored_automatically(webui_context):
    # Check that the code is refactored automatically
    assert webui_context["st"].success.called


@then("the guided refactoring steps should be displayed")
def check_guided_refactoring_steps_displayed(webui_context):
    # Check that the guided refactoring steps are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("I should be able to approve each refactoring step")
def check_approve_refactoring_steps(webui_context):
    # Check that the approval buttons are displayed
    assert webui_context["st"].button.called


@then("the selected refactoring patterns should be applied")
def check_selected_patterns_applied(webui_context):
    # Check that the selected patterns are applied
    assert webui_context["st"].success.called


@then("the refactoring changes should be previewed")
def check_refactoring_changes_previewed(webui_context):
    # Check that the refactoring changes are previewed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("I should be able to accept or reject the changes")
def check_accept_reject_changes(webui_context):
    # Check that the accept/reject buttons are displayed
    assert webui_context["st"].button.called


@then("the refactoring history should be displayed")
def check_refactoring_history_displayed(webui_context):
    # Check that the refactoring history is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("previous refactoring operations should be available for review")
def check_previous_operations_available(webui_context):
    # Check that previous operations are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
