"""
Step definitions for Project Initialization feature.
"""

import os
import sys
import pytest
import shutil
from pytest_bdd import given, when, then, parsers
from unittest.mock import patch, MagicMock

# Import the CLI modules
from devsynth.adapters.cli.typer_adapter import run_cli
from devsynth.application.cli.cli_commands import init_cmd


# Reuse the given step from cli_commands_steps.py
# @given("the DevSynth CLI is installed")
# This is already defined in cli_commands_steps.py


@then(parsers.parse('a new project directory "{directory}" should be created'))
def check_project_directory_created(directory, mock_workflow_manager, tmp_path):
    """
    Verify that a new project directory was created.
    """
    # In our test environment, we're mocking the actual directory creation
    # But we can verify that the init command was called with the correct parameters

    # Extract the name parameter from the command
    # Get the actual call arguments
    args = mock_workflow_manager.execute_command.call_args[0][1]

    # Check that the command was called with the correct name
    assert args.get("name") == directory
    assert args.get("path") == "."

    # In a real implementation, we would check if the directory exists
    # But since we're mocking, we'll just assert that the command was called


@then("the project should use the default layout")
def check_default_structure(mock_workflow_manager):
    """Verify the project uses the single_package layout."""
    assert mock_workflow_manager.execute_command.called
    args = mock_workflow_manager.execute_command.call_args[0][1]
    assert args.get("structure") == "single_package"


@then("a configuration file should be created with default settings")
def check_default_config_created(mock_workflow_manager):
    """Verify that the configuration defaults were applied."""
    assert mock_workflow_manager.execute_command.called
    args = mock_workflow_manager.execute_command.call_args[0][1]
    assert args.get("language") == "python"


@then(parsers.parse("the project should use the {layout} layout"))
def check_custom_layout(layout, mock_workflow_manager):
    """Verify that the selected layout was used."""
    assert mock_workflow_manager.execute_command.called
    args = mock_workflow_manager.execute_command.call_args[0][1]
    assert args.get("structure") == layout


@then(parsers.parse("a configuration file should be created with {lang} settings"))
def check_language_config_created(lang, mock_workflow_manager):
    """Verify that the language choice was recorded."""
    assert mock_workflow_manager.execute_command.called
    args = mock_workflow_manager.execute_command.call_args[0][1]
    assert args.get("language") == lang
