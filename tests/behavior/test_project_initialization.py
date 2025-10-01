"""
Test runner for the Project Initialization feature.
"""

import os

import pytest
from pytest_bdd import scenarios

# Import step definitions
from .steps.cli_commands_steps import *
from .steps.test_project_init_steps import *


pytestmark = [pytest.mark.fast]

# Get the absolute path to the feature file
feature_file = os.path.join(
    os.path.dirname(__file__), "features", "general", "project_initialization.feature"
)

# Define the feature file to test
scenarios(feature_file)


@pytest.fixture(autouse=True)
def _noninteractive_env(monkeypatch):
    """Run initialization scenarios in non-interactive mode."""
    monkeypatch.setenv("DEVSYNTH_NONINTERACTIVE", "1")
    yield
    monkeypatch.delenv("DEVSYNTH_NONINTERACTIVE", raising=False)
