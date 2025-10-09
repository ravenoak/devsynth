"""Test runner for the Project Initialization feature."""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

# Import step definitions
from .steps.cli_commands_steps import *
from .steps.test_project_init_steps import *

pytestmark = [pytest.mark.fast]

# Define the feature file to test via canonical asset paths.
scenarios(feature_path(__file__, "general", "project_initialization.feature"))


@pytest.fixture(autouse=True)
def _noninteractive_env(monkeypatch):
    """Run initialization scenarios in non-interactive mode."""
    monkeypatch.setenv("DEVSYNTH_NONINTERACTIVE", "1")
    yield
    monkeypatch.delenv("DEVSYNTH_NONINTERACTIVE", raising=False)
