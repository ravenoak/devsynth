import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

pytest.skip("Placeholder feature not implemented", allow_module_level=True)

# Import step definitions explicitly to avoid unhashable type errors
from .steps.test_cli_ux_enhancements_steps import (
    check_colorized_output,
    check_completion_suggestions,
    check_detailed_error,
    check_different_colors,
    check_error_docs,
    check_error_suggestion,
    check_help_examples,
    check_help_options,
    check_help_text,
    check_highlighted_warnings,
    check_progress_completion,
    check_progress_indicator,
    check_progress_updates,
    cli_context,
    cli_initialized,
    cli_with_autocompletion,
    run_help_command,
    run_invalid_command,
    run_long_command,
    run_output_command,
    select_completion,
    type_partial_command,
)

pytestmark = [pytest.mark.fast]

# Load scenarios from the feature file
scenarios(feature_path(__file__, "general", "cli_ux_enhancements.feature"))
