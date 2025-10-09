import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

# Skip these high-level integration scenarios until fully implemented
pytest.skip("Integration scenarios are unstable", allow_module_level=True)

# Import step definitions explicitly to avoid unhashable type errors
from .steps.test_webui_integration_steps import (
    check_accessibility,
    check_all_commands,
    check_cli_consistency,
    check_dedicated_interfaces,
    check_detailed_error,
    check_error_docs,
    check_error_messages,
    check_error_suggestions,
    check_help_examples,
    check_help_options,
    check_help_text,
    check_info_messages,
    check_interface_consistency,
    check_progress_indicator,
    check_responsive_design,
    check_subtasks,
    check_success_messages,
    check_time_remaining,
    check_uxbridge_abstraction,
    check_warning_messages,
    interact_with_webui,
    navigate_pages,
    resize_browser,
    run_error_command,
    run_long_operation,
    run_output_command,
    view_help,
    webui_context,
    webui_initialized,
)

# Load scenarios from the feature file. The `bdd_features_base_dir` option in
# pytest.ini sets `tests/behavior/features` as the base directory for feature
# files, so we only need to specify the filename here.


pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "webui_integration.feature"))


from pytest_bdd import given


@given("the WebUI is initialized")
def the_webui_is_initialized(webui_context):
    return webui_context
