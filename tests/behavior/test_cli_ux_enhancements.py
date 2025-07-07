import pytest
from pytest_bdd import scenarios

# Import step definitions explicitly to avoid unhashable type errors
from .steps.cli_ux_enhancements_steps import (
    cli_context,
    cli_initialized,
    run_long_command,
    check_progress_indicator,
    check_progress_updates,
    check_progress_completion,
    run_invalid_command,
    check_detailed_error,
    check_error_suggestion,
    check_error_docs,
    cli_with_autocompletion,
    type_partial_command,
    check_completion_suggestions,
    select_completion,
    run_help_command,
    check_help_text,
    check_help_examples,
    check_help_options,
    run_output_command,
    check_colorized_output,
    check_different_colors,
    check_highlighted_warnings
)

# Load scenarios from the feature file
scenarios("cli_ux_enhancements.feature")
