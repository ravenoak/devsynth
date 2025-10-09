import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "ingestion.feature"))


@then("the ingestion page should be displayed")
def check_ingestion_page(webui_context):
    webui_context["st"].header.assert_any_call("Data Ingestion")


@when("I enter a repository URL")
def enter_repository_url(webui_context):
    webui_context["st"].text_input.return_value = "https://github.com/example/repo.git"


@when("I select a local directory for ingestion")
def select_local_directory(webui_context):
    # Mock the file uploader or directory selector
    webui_context["st"].text_input.return_value = "/path/to/local/directory"


@when("I select a data file for ingestion")
def select_data_file(webui_context):
    # Mock the file uploader
    webui_context["st"].file_uploader = pytest.MagicMock(
        return_value={"name": "data.csv"}
    )


@when("I select a custom parser")
def select_custom_parser(webui_context):
    webui_context["st"].selectbox.return_value = "CustomParser"


@when("I click the ingestion history button")
def click_ingestion_history_button(webui_context):
    # Find the history button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the ingestion settings button")
def click_ingestion_settings_button(webui_context):
    # Find the settings button and set it to return True
    webui_context["st"].button.return_value = True


@when("I update the ingestion settings")
def update_ingestion_settings(webui_context):
    # Mock updating various settings
    webui_context["st"].checkbox.return_value = True
    webui_context["st"].slider.return_value = 50
    webui_context["st"].selectbox.return_value = "Option1"


@when("I save the settings")
def save_settings(webui_context):
    # Find the save button and set it to return True
    webui_context["st"].form_submit_button.return_value = True


@then("the repository code should be ingested")
def check_repository_code_ingested(webui_context):
    # Check that the repository code is ingested
    # This could be implemented by checking that the ingestion function was called
    # or by checking that a success message is displayed
    assert webui_context["st"].success.called


@then("the local code should be ingested")
def check_local_code_ingested(webui_context):
    # Check that the local code is ingested
    assert webui_context["st"].success.called


@then("the data should be ingested")
def check_data_ingested(webui_context):
    # Check that the data is ingested
    assert webui_context["st"].success.called


@then("the data should be ingested with the custom parser")
def check_custom_parser_data_ingested(webui_context):
    # Check that the data is ingested with the custom parser
    assert webui_context["st"].success.called
    # Could add more specific checks for custom parser usage


@then("the ingestion history should be displayed")
def check_ingestion_history_displayed(webui_context):
    # Check that the ingestion history is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("previous ingestion results should be available for review")
def check_previous_results_available(webui_context):
    # Check that previous ingestion results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the ingestion settings should be updated")
def check_ingestion_settings_updated(webui_context):
    # Check that the settings are updated
    # This could be implemented by checking that the settings update function was called
    # or by checking that a success message is displayed
    assert webui_context["st"].success.called
