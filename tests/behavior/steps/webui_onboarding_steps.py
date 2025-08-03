from tests.fixtures.webui_test_utils import (
    mock_streamlit,
    mock_webui,
    simulate_button_click,
    simulate_form_submission,
    simulate_input
)

import pytest
from pytest_bdd import given, when, then, scenarios


@pytest.fixture
def webui_context(mock_webui):
    """
    Fixture that provides a context for WebUI onboarding tests.
    
    This fixture uses the standardized mock_webui fixture from webui_test_utils.py
    to create a consistent testing environment for WebUI onboarding tests.
    
    Args:
        mock_webui: The mock WebUI fixture from webui_test_utils.py
        
    Returns:
        A context dictionary with the mock WebUI instance and related objects
    """
    ui, context = mock_webui
    
    # Set up the sidebar to return "Onboarding" for the navigation
    context['st'].sidebar.radio.return_value = "Onboarding"
    
    # Set up default form values
    simulate_input(context, 'text_input', 'Project Path', '.')
    simulate_input(context, 'text_input', 'Project Root', '.')
    simulate_input(context, 'text_input', 'Primary Language', 'python')
    simulate_input(context, 'text_input', 'Project Goals', 'Build a scalable application')
    
    return context


scenarios("../features/general/webui_onboarding_flow.feature")


@given("the WebUI is initialized")
def _init(webui_context):
    return webui_context


@when('I navigate to "Onboarding"')
def nav_onboarding(webui_context):
    """Navigate to the Onboarding page."""
    # Set up the sidebar to return "Onboarding" for the navigation
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    # Run the WebUI
    webui_context["ui"].run()


@when("I submit the onboarding form")
def submit_onboarding(webui_context):
    """Submit the onboarding form."""
    # Set up the sidebar to return "Onboarding" for the navigation
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    # Simulate form submission
    simulate_form_submission(webui_context, "onboard")
    # Run the WebUI
    webui_context["ui"].run()


@then('the "Project Onboarding" header is shown')
def header_onboarding(webui_context):
    """Verify that the Project Onboarding header is shown."""
    webui_context["st"].header.assert_any_call("Project Onboarding")


@then("the init command should be executed")
def check_init(webui_context):
    """Verify that the init command was executed."""
    assert webui_context["cli"].init_cmd.called, "The init_cmd was not called"

