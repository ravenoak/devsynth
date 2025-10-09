"""Common WebUI step implementations using shared test utilities."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path
from tests.fixtures.webui_test_utils import simulate_form_submission, webui_context

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "webui.feature"))


@given("the WebUI is initialized")
def given_webui_initialized(webui_context):
    """Return the shared WebUI test context."""

    webui_context["st"].session_state.wizard_step = 0
    webui_context["st"].session_state.wizard_data = {}
    return webui_context


@when(parsers.parse('I navigate to "{page}"'))
def navigate_page(webui_context, page: str):
    """Navigate to a specific page in the sidebar."""

    webui_context["st"].sidebar.radio.return_value = page
    webui_context["ui"].run()


@when("I submit the onboarding form")
def submit_onboarding(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    simulate_form_submission(webui_context, "onboard")
    webui_context["ui"].run()


@when("I update a configuration value")
def submit_config(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Config"
    simulate_form_submission(webui_context, "config")
    webui_context["ui"].run()


@when("I submit the edrr cycle form")
def submit_edrr_cycle(webui_context):
    webui_context["st"].sidebar.radio.return_value = "EDRR Cycle"
    simulate_form_submission(webui_context, "edrr")
    webui_context["ui"].run()


@when("I submit the alignment form")
def submit_alignment(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Alignment"
    simulate_form_submission(webui_context, "alignment")
    webui_context["ui"].run()


@when("I submit the alignment metrics form")
def submit_alignment_metrics(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Alignment Metrics"
    simulate_form_submission(webui_context, "alignment-metrics")
    webui_context["ui"].run()


@when("I submit the inspect config form")
def submit_inspect_config(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Inspect Config"
    simulate_form_submission(webui_context, "inspect-config")
    webui_context["ui"].run()


@when("I submit the validate manifest form")
def submit_validate_manifest(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Validate Manifest"
    simulate_form_submission(webui_context, "validate-manifest")
    webui_context["ui"].run()


@when("I submit the validate metadata form")
def submit_validate_metadata(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Validate Metadata"
    simulate_form_submission(webui_context, "validate-metadata")
    webui_context["ui"].run()


@when("I submit the test metrics form")
def submit_test_metrics(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Test Metrics"
    simulate_form_submission(webui_context, "test-metrics")
    webui_context["ui"].run()


@when("I submit the generate docs form")
def submit_generate_docs(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Generate Docs"
    simulate_form_submission(webui_context, "generate-docs")
    webui_context["ui"].run()


@when("I submit the ingest form")
def submit_ingest(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Ingest"
    simulate_form_submission(webui_context, "ingest")
    webui_context["ui"].run()


@when("I submit the api spec form")
def submit_api_spec(webui_context):
    webui_context["st"].sidebar.radio.return_value = "API Spec"
    simulate_form_submission(webui_context, "api-spec")
    webui_context["ui"].run()


@then(parsers.parse('the "{header}" header is shown'))
def check_header(header: str, webui_context):
    webui_context["st"].header.assert_any_call(header)


@then("the init command should be executed")
def check_init(webui_context):
    assert webui_context["cli"].init_cmd.called


@then("the config command should be executed")
def check_config(webui_context):
    assert webui_context["cli"].config_cmd.called


@then("the edrr_cycle command should be executed")
def check_edrr_cycle(webui_context):
    assert webui_context["cli"].edrr_cycle_cmd.called


@then("the align command should be executed")
def check_align(webui_context):
    assert webui_context["cli"].align_cmd.called


@then("the alignment_metrics command should be executed")
def check_alignment_metrics(webui_context):
    assert webui_context["cli"].alignment_metrics_cmd.called


@then("the inspect_config command should be executed")
def check_inspect_config(webui_context):
    assert webui_context["cli"].inspect_config_cmd.called


@then("the validate_manifest command should be executed")
def check_validate_manifest(webui_context):
    assert webui_context["cli"].validate_manifest_cmd.called


@then("the validate_metadata command should be executed")
def check_validate_metadata(webui_context):
    assert webui_context["cli"].validate_metadata_cmd.called


@then("the test_metrics command should be executed")
def check_test_metrics(webui_context):
    assert webui_context["cli"].test_metrics_cmd.called


@then("the generate_docs command should be executed")
def check_generate_docs(webui_context):
    assert webui_context["cli"].generate_docs_cmd.called


@then("the ingest command should be executed")
def check_ingest(webui_context):
    assert webui_context["cli"].ingest_cmd.called


@then("the apispec command should be executed")
def check_apispec(webui_context):
    assert webui_context["cli"].apispec_cmd.called
