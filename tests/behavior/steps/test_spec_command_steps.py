"""Steps for the spec command feature."""

import os
import pytest
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from pytest_bdd import when, then, parsers

# Get the absolute path to the feature file using pathlib for better path handling
current_dir = Path(__file__).parent
feature_file = str(current_dir.parent / "features" / "spec_command.feature")

# Define a simple feature string in case the file can't be loaded
FEATURE = """
Feature: Spec Command
  As a developer
  I want to generate specifications from requirements
  So that I can create a structured development plan

  Scenario: Generate specifications from requirements file
    When I run the command "devsynth spec --requirements-file requirements.md"
    Then the spec command should process "requirements.md"
"""

# Write the feature to a temporary file if needed
if not os.path.exists(feature_file):
    print(f"Feature file {feature_file} not found, creating a simple version")
    with open(feature_file, "w") as f:
        f.write(FEATURE)

# Create a temporary feature file in the current directory as a fallback
temp_feature_file = os.path.join(os.path.dirname(__file__), "temp_spec_command.feature")
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


@when(parsers.parse('I run the command "devsynth spec --requirements-file {req_file}"'))
def run_spec_command(req_file, command_context):
    """Invoke the spec command with a requirements file."""
    from devsynth.application.cli.cli_commands import spec_cmd

    captured_output = StringIO()
    with patch("sys.stdout", new=captured_output):
        spec_cmd(requirements_file=req_file)

    command_context["output"] = captured_output.getvalue()


@then(parsers.parse('the spec command should process "{req_file}"'))
def check_spec_called(req_file, mock_workflow_manager):
    """Verify the workflow manager received the spec command."""
    mock_workflow_manager.execute_command.assert_any_call(
        "spec", {"requirements_file": req_file}
    )
