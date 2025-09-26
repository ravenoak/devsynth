"""
Test runner for the Requirement Analysis feature.
"""

import os

import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *

# Import the step definitions
from .steps.test_requirement_analysis_steps import *

pytestmark = [pytest.mark.fast]

# Get the absolute path to the feature file
base_dir = os.path.join(os.path.dirname(__file__), "features")
feature_file = os.path.join(base_dir, "general", "requirement_analysis.feature")
feature_file_spec = os.path.join(base_dir, "requirement_analysis.feature")

# Define the scenarios to test
scenarios(feature_file)
scenarios(feature_file_spec)
