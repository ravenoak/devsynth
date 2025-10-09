import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "docs_generation.feature"))


@then("the docs generation page should be displayed")
def check_docs_generation_page(webui_context):
    webui_context["st"].header.assert_any_call("Documentation Generation")


@when("I select a custom documentation template")
def select_custom_template(webui_context):
    webui_context["st"].selectbox.return_value = "CustomTemplate"


@when("I select specific components for documentation")
def select_specific_components(webui_context):
    # Mock the multiselect function if it's used in the page
    webui_context["st"].multiselect = pytest.MagicMock(
        return_value=["Component1", "Component2"]
    )


@when("I click the preview button")
def click_preview_button(webui_context):
    # Find the preview button in columns and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False


@when("I select a documentation format")
def select_documentation_format(webui_context):
    webui_context["st"].selectbox.return_value = "Markdown"


@when("I click the export button")
def click_export_button(webui_context):
    # Find the export button in columns and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col2_mock.button.return_value = True
    col1_mock.button.return_value = False


@when("I click the generation history button")
def click_generation_history_button(webui_context):
    # Find the history button and set it to return True
    webui_context["st"].button.return_value = True


@then("the documentation should be generated")
def check_documentation_generated(webui_context):
    # Check that the documentation is generated
    # This could be implemented by checking that the generation function was called
    # or by checking that a success message is displayed
    assert webui_context["st"].success.called


@then("the documentation should be generated with the custom template")
def check_custom_template_documentation_generated(webui_context):
    # Check that the documentation is generated with the custom template
    assert webui_context["st"].success.called
    # Could add more specific checks for custom template usage


@then("the documentation should be generated for the selected components")
def check_component_documentation_generated(webui_context):
    # Check that the documentation is generated for the selected components
    assert webui_context["st"].success.called
    # Could add more specific checks for component-specific documentation


@then("the generated documentation should be previewed")
def check_documentation_previewed(webui_context):
    # Check that the documentation preview is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the documentation should be exported in the selected format")
def check_documentation_exported(webui_context):
    # Check that a success message is shown after export
    webui_context["st"].success.assert_called_once()


@then("the documentation generation history should be displayed")
def check_generation_history_displayed(webui_context):
    # Check that the generation history is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("previous generation results should be available for review")
def check_previous_results_available(webui_context):
    # Check that previous generation results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
