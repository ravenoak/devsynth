import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from .test_webui_steps import given_webui_initialized, webui_context

# Import the scenarios from the feature file
scenarios("../features/webui/inspect_config.feature")


@pytest.mark.medium
@then("the inspect config page should be displayed")
def check_inspect_config_page(webui_context):
    webui_context["st"].header.assert_any_call("Inspect Configuration")


@pytest.mark.medium
@when("I select a specific configuration category")
def select_config_category(webui_context):
    webui_context["st"].selectbox.return_value = "SelectedCategory"


@pytest.mark.medium
@when("I enter a search term in the configuration search field")
def enter_search_term(webui_context):
    webui_context["st"].text_input.return_value = "search_term"


@pytest.mark.medium
@when("I click the export config button")
def click_export_config(webui_context):
    # Find the export button in columns and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False


@pytest.mark.medium
@when('I enable the "Compare with defaults" option')
def enable_compare_defaults(webui_context):
    webui_context["st"].checkbox.return_value = True


@pytest.mark.medium
@then("the configuration details should be displayed")
def check_config_details_displayed(webui_context):
    # Check that the configuration details are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@pytest.mark.medium
@then("the filtered configuration details should be displayed")
def check_filtered_config_displayed(webui_context):
    # Check that the filtered configuration details are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks based on the actual implementation


@pytest.mark.medium
@then("the matching configuration keys should be displayed")
def check_matching_keys_displayed(webui_context):
    # Check that the matching keys are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for search results


@pytest.mark.medium
@then("the configuration report should be exported")
def check_config_report_exported(webui_context):
    # Check that a success message is shown after export
    webui_context["st"].success.assert_called_once()


@pytest.mark.medium
@then("the configuration comparison should be displayed")
def check_comparison_displayed(webui_context):
    # Check that comparison results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@pytest.mark.medium
@then("differences from default values should be highlighted")
def check_differences_highlighted(webui_context):
    # Check that differences are highlighted (could be implemented in various ways)
    # This is a simplified check that assumes some form of display is used
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
