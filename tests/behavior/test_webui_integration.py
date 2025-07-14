import pytest
from pytest_bdd import scenarios

# Import step definitions explicitly to avoid unhashable type errors
from .steps.webui_integration_steps import (
    webui_context,
    webui_initialized,
    run_long_operation,
    check_progress_indicator,
    check_time_remaining,
    check_subtasks,
    run_output_command,
    check_success_messages,
    check_warning_messages,
    check_error_messages,
    check_info_messages,
    run_error_command,
    check_detailed_error,
    check_error_suggestions,
    check_error_docs,
    view_help,
    check_help_text,
    check_help_examples,
    check_help_options,
    interact_with_webui,
    check_uxbridge_abstraction,
    check_cli_consistency,
    resize_browser,
    check_responsive_design,
    check_accessibility,
    navigate_pages,
    check_all_commands,
    check_dedicated_interfaces,
    check_interface_consistency
)

# Load scenarios from the feature file. The `bdd_features_base_dir` option in
# pytest.ini sets `tests/behavior/features` as the base directory for feature
# files, so we only need to specify the filename here.
scenarios("webui_integration.feature")
