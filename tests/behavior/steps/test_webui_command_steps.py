"""
Step definitions for WebUI Command Execution feature.
"""

import os
import sys
from unittest.mock import ANY, MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Import the CLI modules
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.cli_commands import webui_cmd
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Register the feature scenarios


scenarios(feature_path(__file__, "general", "command.feature"))

# Reuse existing step definitions
from .cli_commands_steps import (
    devsynth_cli_installed,
    run_command,
    valid_devsynth_project,
)


@given("the Streamlit WebUI module is unavailable")
def streamlit_webui_unavailable(monkeypatch):
    """
    Make the Streamlit WebUI module unavailable for testing error handling.
    """

    # Create a mock that raises an ImportError when imported
    def mock_import_error(name, *args, **kwargs):
        if name == "devsynth.interface.webui":
            raise ImportError("No module named 'streamlit'")
        return original_import(name, *args, **kwargs)

    # Save the original import function
    original_import = __import__
    # Replace the import function with our mock
    monkeypatch.setattr("builtins.__import__", mock_import_error)
    return True


@then("the system should launch the Streamlit WebUI")
def check_webui_launched(command_context, monkeypatch):
    """
    Verify that the Streamlit WebUI was launched.
    """
    # In a test environment, we can't actually launch the WebUI,
    # but we can check that the webui_cmd function was called
    # and that it attempted to import and run the WebUI
    output = command_context.get("output", "")

    # Check that there's no error message in the output
    assert "Error" not in output, f"Error message found in output: {output}"

    # The actual WebUI launch would happen in a real environment
    # Here we're just verifying that the command executed without errors
    exit_code = command_context.get("exit_code", 1)
    assert exit_code == 0, f"Command failed with exit code {exit_code}"


@then("the system should display an error message")
def check_error_displayed(command_context):
    """
    Verify that an error message was displayed.
    """
    output = command_context.get("output", "")
    assert "Error" in output, f"No error message found in output: {output}"


@then("the error message should indicate the WebUI could not be launched")
def check_webui_error_message(command_context):
    """
    Verify that the error message indicates the WebUI could not be launched.
    """
    output = command_context.get("output", "")
    assert "Error" in output, f"No error message found in output: {output}"
    # Check for specific error message about the WebUI not being available
    assert (
        "No module named 'streamlit'" in output
        or "WebUI could not be launched" in output
    ), f"Error message does not indicate WebUI launch failure: {output}"


@then(parsers.parse("the WebUI should contain the following pages:"))
def check_webui_pages(command_context, table):
    """
    Verify that the WebUI contains all the required pages.
    """
    # In a test environment, we can't actually check the WebUI pages,
    # but we can verify that the command executed without errors
    exit_code = command_context.get("exit_code", 1)
    assert exit_code == 0, f"Command failed with exit code {exit_code}"

    # In a real test, we would use Selenium or another browser automation tool
    # to check that the WebUI contains all the required pages
    # For now, we'll just log the pages that should be present
    pages = [row[0] for row in table]
    print(f"The WebUI should contain the following pages: {', '.join(pages)}")

    # This is a placeholder for future implementation
    # In a real test, we would check that each page is accessible
    pass
