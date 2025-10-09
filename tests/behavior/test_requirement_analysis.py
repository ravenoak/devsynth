"""Test runner for the Requirement Analysis feature."""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.cli_commands_steps import *

# Import the step definitions
from .steps.test_requirement_analysis_steps import *

pytestmark = [pytest.mark.fast]

# Define the scenarios to test via the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "requirement_analysis.feature"))
