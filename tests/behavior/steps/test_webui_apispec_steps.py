import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "apispec.feature"))


@then("the APISpec page should be displayed")
def check_apispec_page(webui_context):
    webui_context["st"].header.assert_any_call("API Specification")


@when("I select source code for API specification")
def select_source_code(webui_context):
    # Mock the file uploader or directory selector
    webui_context["st"].text_input.return_value = "/path/to/source/code"


@when("I select a custom API specification format")
def select_custom_format(webui_context):
    webui_context["st"].selectbox.return_value = "Custom Format"


@when("I select an existing API specification")
def select_existing_specification(webui_context):
    webui_context["st"].selectbox.return_value = "ExistingSpec"


@when("I make changes to the specification")
def make_changes_to_specification(webui_context):
    webui_context["st"].text_area.return_value = "Modified API Specification"


@when("I save the changes")
def save_changes(webui_context):
    webui_context["st"].form_submit_button.return_value = True


@when("I click the validate button")
def click_validate_button(webui_context):
    # Find the validate button and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False


@when("I click the export button")
def click_export_button(webui_context):
    # Find the export button and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col2_mock.button.return_value = True
    col1_mock.button.return_value = False


@when("I select a target language for client code")
def select_target_language(webui_context):
    webui_context["st"].selectbox.return_value = "Python"


@when("I click the generate client button")
def click_generate_client_button(webui_context):
    # Find the generate client button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the specification history button")
def click_specification_history_button(webui_context):
    # Find the history button and set it to return True
    webui_context["st"].button.return_value = True


@then("the API specification should be generated")
def check_specification_generated(webui_context):
    # Check that the API specification is generated
    # This could be implemented by checking that the generation function was called
    # or by checking that a success message is displayed
    assert webui_context["st"].success.called


@then("the API specification should be generated in the selected format")
def check_format_specification_generated(webui_context):
    # Check that the API specification is generated in the selected format
    assert webui_context["st"].success.called
    # Could add more specific checks for format-specific generation


@then("the API specification should be updated")
def check_specification_updated(webui_context):
    # Check that the API specification is updated
    assert webui_context["st"].success.called


@then("the API specification validation results should be displayed")
def check_validation_results_displayed(webui_context):
    # Check that the validation results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the API specification should be exported")
def check_specification_exported(webui_context):
    # Check that a success message is shown after export
    webui_context["st"].success.assert_called_once()


@then("the client code should be generated")
def check_client_code_generated(webui_context):
    # Check that the client code is generated
    assert webui_context["st"].success.called


@then("the API specification history should be displayed")
def check_specification_history_displayed(webui_context):
    # Check that the specification history is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("previous versions should be available for review")
def check_previous_versions_available(webui_context):
    # Check that previous versions are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
