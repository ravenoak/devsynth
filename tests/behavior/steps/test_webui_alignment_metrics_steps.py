import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "alignment_metrics.feature"))


@then("the alignment metrics page should be displayed")
def check_alignment_metrics_page(webui_context):
    webui_context["st"].header.assert_any_call("Alignment Metrics")


@when("I select a specific component for alignment analysis")
def select_component_for_alignment(webui_context):
    webui_context["st"].selectbox.return_value = "SelectedComponent"


@when("I click the export report button")
def click_export_report(webui_context):
    # Find the export button in columns and set it to return True
    col1_mock, col2_mock = webui_context["st"].columns.return_value
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False


@when("I click the visualization tab")
def click_visualization_tab(webui_context):
    webui_context["st"].selectbox.return_value = "Visualization"


@when("I select multiple versions for comparison")
def select_multiple_versions(webui_context):
    # Mock the multiselect function if it's used in the page
    webui_context["st"].multiselect = pytest.MagicMock(return_value=["v1.0", "v2.0"])


@then("the alignment metrics should be displayed")
def check_alignment_metrics_displayed(webui_context):
    # Check that the metrics are displayed using write or markdown
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the filtered alignment metrics should be displayed")
def check_filtered_metrics_displayed(webui_context):
    # Check that the filtered metrics are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks based on the actual implementation


@then("the alignment metrics report should be exported")
def check_report_exported(webui_context):
    # Check that a success message is shown after export
    webui_context["st"].success.assert_called_once()


@then("the alignment metrics visualization should be displayed")
def check_visualization_displayed(webui_context):
    # Check that visualization components are used
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for visualization components


@then("the alignment metrics comparison should be displayed")
def check_comparison_displayed(webui_context):
    # Check that comparison results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for comparison display
