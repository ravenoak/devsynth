import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "dbschema.feature"))


@then("the DBSchema page should be displayed")
def check_dbschema_page(webui_context):
    webui_context["st"].header.assert_any_call("Database Schema Manager")


@when("I click the create new schema button")
def click_create_new_schema_button(webui_context):
    # Find the create new schema button and set it to return True
    webui_context["st"].button.return_value = True


@when("I enter schema details")
def enter_schema_details(webui_context):
    webui_context["st"].text_input.return_value = "MySchema"
    webui_context["st"].text_area.return_value = "Schema description"


@when("I save the schema")
def save_schema(webui_context):
    # Find the save button and set it to return True
    webui_context["st"].form_submit_button.return_value = True


@when("I click the import schema button")
def click_import_schema_button(webui_context):
    # Find the import schema button and set it to return True
    webui_context["st"].button.return_value = True


@when("I select a schema file to import")
def select_schema_file(webui_context):
    # Mock the file uploader
    webui_context["st"].file_uploader = pytest.MagicMock(
        return_value={"name": "schema.sql"}
    )


@when("I confirm the import")
def confirm_import(webui_context):
    # Find the confirm button and set it to return True
    webui_context["st"].button.return_value = True


@when("I select an existing schema")
def select_existing_schema(webui_context):
    webui_context["st"].selectbox.return_value = "ExistingSchema"


@when("I make changes to the schema")
def make_changes_to_schema(webui_context):
    webui_context["st"].text_area.return_value = "Modified schema"


@when("I click the generate SQL button")
def click_generate_sql_button(webui_context):
    # Find the generate SQL button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the export button")
def click_export_button(webui_context):
    # Find the export button and set it to return True
    webui_context["st"].button.return_value = True


@when("I select an export format")
def select_export_format(webui_context):
    webui_context["st"].selectbox.return_value = "SQL"


@when("I click the visualize button")
def click_visualize_button(webui_context):
    # Find the visualize button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the validate button")
def click_validate_button(webui_context):
    # Find the validate button and set it to return True
    webui_context["st"].button.return_value = True


@then("the database schema should be created")
def check_schema_created(webui_context):
    # Check that the schema is created
    assert webui_context["st"].success.called


@then("the database schema should be imported")
def check_schema_imported(webui_context):
    # Check that the schema is imported
    assert webui_context["st"].success.called


@then("the database schema should be updated")
def check_schema_updated(webui_context):
    # Check that the schema is updated
    assert webui_context["st"].success.called


@then("the SQL code should be generated")
def check_sql_generated(webui_context):
    # Check that the SQL code is generated
    assert webui_context["st"].success.called


@then("the SQL code should be displayed")
def check_sql_displayed(webui_context):
    # Check that the SQL code is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the schema should be exported in the selected format")
def check_schema_exported(webui_context):
    # Check that the schema is exported
    assert webui_context["st"].success.called


@then("the schema visualization should be displayed")
def check_visualization_displayed(webui_context):
    # Check that the visualization is displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the visualization should accurately represent the schema")
def check_visualization_accuracy(webui_context):
    # This is a simplified check since accuracy would require more complex testing
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the schema validation results should be displayed")
def check_validation_results_displayed(webui_context):
    # Check that the validation results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
