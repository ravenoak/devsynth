import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "webapp.feature"))


@then("the WebApp page should be displayed")
def check_webapp_page(webui_context):
    webui_context["st"].header.assert_any_call("Web Application Generator")


@when("I enter web application details")
def enter_webapp_details(webui_context):
    webui_context["st"].text_input.return_value = "My Web App"
    webui_context["st"].text_area.return_value = "Web application description"


@when("I select a custom web application template")
def select_custom_template(webui_context):
    webui_context["st"].selectbox.return_value = "Custom Template"


@when("I select specific UI components")
def select_specific_components(webui_context):
    # Mock the multiselect function if it's used in the page
    webui_context["st"].multiselect = pytest.MagicMock(
        return_value=["Component1", "Component2"]
    )


@when("I submit the WebApp form")
def submit_webapp_form(webui_context):
    webui_context["st"].form_submit_button.return_value = True


@when("I click the preview button")
def click_preview_button(webui_context):
    # Find the preview button and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False


@when("I select an existing web application")
def select_existing_webapp(webui_context):
    webui_context["st"].selectbox.return_value = "Existing Web App"


@when("I click the deploy button")
def click_deploy_button(webui_context):
    # Find the deploy button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the settings button")
def click_settings_button(webui_context):
    # Find the settings button and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col2_mock.button.return_value = True
    col1_mock.button.return_value = False


@when("I update the web application settings")
def update_webapp_settings(webui_context):
    # Mock updating various settings
    webui_context["st"].checkbox.return_value = True
    webui_context["st"].slider.return_value = 50
    webui_context["st"].selectbox.return_value = "Option1"


@when("I save the settings")
def save_settings(webui_context):
    # Find the save button and set it to return True
    webui_context["st"].form_submit_button.return_value = True


@when("I click the generation history button")
def click_generation_history_button(webui_context):
    # Find the history button and set it to return True
    webui_context["st"].button.return_value = True


@then("the web application should be generated")
def check_webapp_generated(webui_context):
    # Check that the web application is generated
    assert webui_context["st"].success.called


@then("the web application should be generated with the custom template")
def check_custom_template_webapp_generated(webui_context):
    # Check that the web application is generated with the custom template
    assert webui_context["st"].success.called
    # Could add more specific checks for custom template usage


@then("the web application should be generated with the selected components")
def check_component_webapp_generated(webui_context):
    # Check that the web application is generated with the selected components
    assert webui_context["st"].success.called
    # Could add more specific checks for component-specific generation


@then("the generated web application should be previewed")
def check_webapp_previewed(webui_context):
    # Check that the web application preview is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the web application should be deployed")
def check_webapp_deployed(webui_context):
    # Check that the web application is deployed
    assert webui_context["st"].success.called


@then("the web application settings should be updated")
def check_webapp_settings_updated(webui_context):
    # Check that the settings are updated
    assert webui_context["st"].success.called


@then("the web application generation history should be displayed")
def check_generation_history_displayed(webui_context):
    # Check that the generation history is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("previous generation results should be available for review")
def check_previous_results_available(webui_context):
    # Check that previous generation results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
