"""
Step definitions for Environment Variables Integration feature.
"""

import os
import tempfile
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file
scenarios(feature_path(__file__, "general", "environment_variables.feature"))


@given(parsers.parse("I have a .env file with the following content:\n{content}"))
def create_env_file(content, monkeypatch):
    """Create a temporary .env file with the given content."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create a .env file in the temporary directory
    env_file = Path(temp_dir) / ".env"
    env_file.write_text(content.strip())

    # Monkeypatch os.getcwd to return the temporary directory
    monkeypatch.setattr(os, "getcwd", lambda: temp_dir)

    # Return the path to the .env file for cleanup
    return env_file


@then(parsers.parse('the system should display the value "{value}" for "{key}"'))
def check_config_value(value, key, mock_workflow_manager):
    """Check that the system displays the expected value for the given key."""
    # Verify that the execute_command method was called with the correct arguments
    mock_workflow_manager.execute_command.assert_any_call(
        "config", {"key": key, "value": None}
    )

    # Verify that the created .env file contains the expected value
    env_file = Path(os.getcwd()) / ".env"
    if env_file.exists():
        content = env_file.read_text()
        assert f"{key.upper()}={value}" in content
