import pytest
from pytest_bdd import given, when, then, scenarios, parsers

from .test_webui_steps import webui_context, given_webui_initialized

# Import the scenarios from the feature file
scenarios("../features/webui_validate_metadata.feature")


@pytest.mark.medium
@then("the validate metadata page should be displayed")
def check_validate_metadata_page(webui_context):
    webui_context["st"].header.assert_any_call("Validate Metadata")


@pytest.mark.medium
@when("I select a specific metadata schema")
def select_metadata_schema(webui_context):
    webui_context["st"].selectbox.return_value = "SelectedSchema"


@pytest.mark.medium
@when("I select a metadata template for comparison")
def select_metadata_template(webui_context):
    webui_context["st"].selectbox.return_value = "SelectedTemplate"


@pytest.mark.medium
@then("the metadata validation results should be displayed")
def check_validation_results_displayed(webui_context):
    # Check that the validation results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@pytest.mark.medium
@then("the metadata validation results with the selected schema should be displayed")
def check_schema_validation_results_displayed(webui_context):
    # Check that the validation results with the selected schema are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks based on the actual implementation


@pytest.mark.medium
@then("the metadata issues should be fixed automatically")
def check_issues_fixed(webui_context):
    # Check that the issues are fixed
    # This could be implemented by checking that the auto-fix function was called
    # or by checking that a success message is displayed
    assert webui_context["st"].success.called


@pytest.mark.medium
@then("the metadata validation report should be exported")
def check_validation_report_exported(webui_context):
    # Check that a success message is shown after export
    webui_context["st"].success.assert_called_once()


@pytest.mark.medium
@then("the metadata validation history should be displayed")
def check_validation_history_displayed(webui_context):
    # Check that the validation history is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@pytest.mark.medium
@then("previous validation results should be available for review")
def check_previous_results_available(webui_context):
    # Check that previous validation results are displayed
    # This could be implemented by checking that the history data is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@pytest.mark.medium
@then("the metadata comparison results should be displayed")
def check_comparison_results_displayed(webui_context):
    # Check that the comparison results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@pytest.mark.medium
@then("differences from the template should be highlighted")
def check_differences_highlighted(webui_context):
    # Check that differences are highlighted
    # This could be implemented by checking that the highlighting function was called
    # or by checking that the differences are displayed in a specific way
    assert webui_context["st"].write.called or webui_context["st"].markdown.called