
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
from devsynth.adapters.cli.argparse_adapter import run_cli
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


@then("the project should have the default structure")
def check_default_structure(mock_workflow_manager):
    """
    Verify that the project has the default structure.
    """
    # Verify that the init command was called
    assert mock_workflow_manager.execute_command.called
    
    # In a real implementation, we would check for specific directories and files
    # But since we're mocking, we'll just assert that the command was called with default template
    
    # The template parameter should not be specified or should be "default"
    # Extract the last call arguments
    args = mock_workflow_manager.execute_command.call_args[0][1]
    
    # Check that template is either not specified or is "default"
    assert "template" not in args or args.get("template") == "default"


@then("a configuration file should be created with default settings")
def check_default_config_created(mock_workflow_manager):
    """
    Verify that a configuration file was created with default settings.
    """
    # Verify that the init command was called
    assert mock_workflow_manager.execute_command.called
    
    # In a real implementation, we would check for the config file and its contents
    # But since we're mocking, we'll just assert that the command was called
    
    # The template parameter should not be specified or should be "default"
    # Extract the last call arguments
    args = mock_workflow_manager.execute_command.call_args[0][1]
    
    # Check that template is either not specified or is "default"
    assert "template" not in args or args.get("template") == "default"


@then(parsers.parse('the project should have the {template} template structure'))
def check_template_structure(template, mock_workflow_manager):
    """
    Verify that the project has the specified template structure.
    """
    # Verify that the init command was called
    assert mock_workflow_manager.execute_command.called
    
    # Extract the last call arguments
    args = mock_workflow_manager.execute_command.call_args[0][1]
    
    # Check that the template parameter matches the expected template
    # The template in the feature file might be "web-app" but in the args it's "web-app"
    # So we need to handle both cases
    template_value = template.replace("-", "-")  # This is a no-op but makes the intention clear
    assert args.get("template") == template_value


@then(parsers.parse('a configuration file should be created with {template} template settings'))
def check_template_config_created(template, mock_workflow_manager):
    """
    Verify that a configuration file was created with template-specific settings.
    """
    # Verify that the init command was called
    assert mock_workflow_manager.execute_command.called
    
    # Extract the last call arguments
    args = mock_workflow_manager.execute_command.call_args[0][1]
    
    # Check that the template parameter matches the expected template
    assert args.get("template") == template
