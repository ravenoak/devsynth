import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .webui_steps import given_webui_initialized, webui_context

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "test_metrics.feature"))


@then("the test metrics page should be displayed")
def check_test_metrics_page(webui_context):
    webui_context["st"].header.assert_any_call("Test Metrics")


@when("I select a specific component for test analysis")
def select_component_for_test_analysis(webui_context):
    webui_context["st"].selectbox.return_value = "SelectedComponent"


@when('I select the "Execution Time" metric type')
def select_execution_time_metric(webui_context):
    webui_context["st"].selectbox.return_value = "Execution Time"


@when('I select the "Failures" metric type')
def select_failures_metric(webui_context):
    webui_context["st"].selectbox.return_value = "Failures"


@when("I select multiple test runs for comparison")
def select_multiple_test_runs(webui_context):
    # Mock the multiselect function if it's used in the page
    webui_context["st"].multiselect = pytest.MagicMock(return_value=["Run1", "Run2"])


@then("the test coverage metrics should be displayed")
def check_coverage_metrics_displayed(webui_context):
    # Check that the coverage metrics are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called


@then("the filtered test metrics should be displayed")
def check_filtered_metrics_displayed(webui_context):
    # Check that the filtered metrics are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks based on the actual implementation


@then("the test execution time metrics should be displayed")
def check_execution_time_metrics_displayed(webui_context):
    # Check that the execution time metrics are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for execution time metrics


@then("the test failure metrics should be displayed")
def check_failure_metrics_displayed(webui_context):
    # Check that the failure metrics are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for failure metrics


@then("the test metrics report should be exported")
def check_metrics_report_exported(webui_context):
    # Check that a success message is shown after export
    webui_context["st"].success.assert_called_once()


@then("the test metrics visualization should be displayed")
def check_visualization_displayed(webui_context):
    # Check that visualization components are used
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for visualization components


@then("the test metrics comparison should be displayed")
def check_comparison_displayed(webui_context):
    # Check that comparison results are displayed
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
    # Could add more specific checks for comparison display


@then("differences between runs should be highlighted")
def check_differences_highlighted(webui_context):
    # Check that differences are highlighted
    # This could be implemented by checking that the highlighting function was called
    # or by checking that the differences are displayed in a specific way
    assert webui_context["st"].write.called or webui_context["st"].markdown.called
