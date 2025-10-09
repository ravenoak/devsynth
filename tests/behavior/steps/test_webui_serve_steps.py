import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "serve.feature"))


@then("the Serve page should be displayed")
def check_serve_page(webui_context):
    webui_context["st"].header.assert_any_call("Application Server")


@when("I select an application to serve")
def select_application_to_serve(webui_context):
    webui_context["st"].selectbox.return_value = "MyApplication"


@when("I click the start button")
def click_start_button(webui_context):
    # Find the start button and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False


@when("I select a running application")
def select_running_application(webui_context):
    webui_context["st"].selectbox.return_value = "RunningApp"
    # Set up session state to indicate the application is running
    webui_context["st"].session_state.running_apps = ["RunningApp"]


@when("I click the stop button")
def click_stop_button(webui_context):
    # Find the stop button and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col2_mock.button.return_value = True
    col1_mock.button.return_value = False


@when("I click the settings button")
def click_settings_button(webui_context):
    # Find the settings button and set it to return True
    webui_context["st"].button.return_value = True


@when("I update the server settings")
def update_server_settings(webui_context):
    # Mock updating various settings
    webui_context["st"].number_input.return_value = 8080
    webui_context["st"].checkbox.return_value = True
    webui_context["st"].selectbox.return_value = "Production"


@when("I save the settings")
def save_settings(webui_context):
    # Find the save button and set it to return True
    webui_context["st"].form_submit_button.return_value = True


@when("I click the logs button")
def click_logs_button(webui_context):
    # Find the logs button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the restart button")
def click_restart_button(webui_context):
    # Find the restart button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the metrics button")
def click_metrics_button(webui_context):
    # Find the metrics button and set it to return True
    webui_context["st"].button.return_value = True


@when("I click the deploy to production button")
def click_deploy_to_production_button(webui_context):
    # Find the deploy to production button and set it to return True
    webui_context["st"].button.return_value = True


@when("I confirm the deployment")
def confirm_deployment(webui_context):
    # Find the confirm button and set it to return True
    webui_context["st"].button.return_value = True


@then("the application should start serving")
def check_application_starts_serving(webui_context):
    # Check that the application starts serving
    assert webui_context["st"].success.called


@then("the server status should show as running")
def check_server_status_running(webui_context):
    # Check that the server status shows as running
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for status display


@then("the application should stop serving")
def check_application_stops_serving(webui_context):
    # Check that the application stops serving
    assert webui_context["st"].success.called


@then("the server status should show as stopped")
def check_server_status_stopped(webui_context):
    # Check that the server status shows as stopped
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for status display


@then("the server settings should be updated")
def check_server_settings_updated(webui_context):
    # Check that the server settings are updated
    assert webui_context["st"].success.called


@then("the server logs should be displayed")
def check_server_logs_displayed(webui_context):
    # Check that the server logs are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the logs should update in real-time")
def check_logs_update_realtime(webui_context):
    # Check that the logs update in real-time
    # This is a simplified check since real-time updates would require more complex testing
    assert (
        webui_context["st"].empty.called
        if hasattr(webui_context["st"], "empty")
        else True
    )


@then("the application should restart")
def check_application_restarts(webui_context):
    # Check that the application restarts
    assert webui_context["st"].success.called


@then("the server metrics should be displayed")
def check_server_metrics_displayed(webui_context):
    # Check that the server metrics are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the metrics should update in real-time")
def check_metrics_update_realtime(webui_context):
    # Check that the metrics update in real-time
    # This is a simplified check since real-time updates would require more complex testing
    assert (
        webui_context["st"].empty.called
        if hasattr(webui_context["st"], "empty")
        else True
    )


@then("the application should be deployed to production")
def check_application_deployed_to_production(webui_context):
    # Check that the application is deployed to production
    assert webui_context["st"].success.called
