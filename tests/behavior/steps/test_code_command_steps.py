"""Steps for the code command feature."""

import os
import pytest
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from pytest_bdd import when, then

# Get the absolute path to the feature file using pathlib for better path handling
current_dir = Path(__file__).parent
feature_file = str(current_dir.parent / "features" / "code_command.feature")

# Define a simple feature string in case the file can't be loaded
FEATURE = """
Feature: Code Command
  As a developer
  I want to generate code from tests
  So that I can implement functionality that passes the tests

  Scenario: Generate code from tests
    When I run the command "devsynth code"
    Then the code command should be executed
"""

# Write the feature to a temporary file if needed
if not os.path.exists(feature_file):
    print(f"Feature file {feature_file} not found, creating a simple version")
    with open(feature_file, "w") as f:
        f.write(FEATURE)

# Create a temporary feature file in the current directory as a fallback
temp_feature_file = os.path.join(os.path.dirname(__file__), "temp_code_command.feature")
with open(temp_feature_file, "w") as f:
    f.write(FEATURE)

# Use a pytest hook to register scenarios when the test session starts
def pytest_configure(config):
    """Register scenarios when the test session starts."""
    from pytest_bdd import scenarios
    try:
        scenarios(feature_file)
    except Exception as e:
        print(f"Error loading scenarios from {feature_file}: {e}")
        scenarios(temp_feature_file)


@when('I run the command "devsynth code"')
def run_code_command(command_context):
    """Invoke the code command."""
    from devsynth.application.cli.cli_commands import code_cmd

    captured_output = StringIO()
    with patch("sys.stdout", new=captured_output):
        code_cmd()

    command_context["output"] = captured_output.getvalue()


@then("the code command should be executed")
def check_code_called(mock_workflow_manager):
    """Verify the workflow manager executed the code command."""
    mock_workflow_manager.execute_command.assert_any_call("code", {})
