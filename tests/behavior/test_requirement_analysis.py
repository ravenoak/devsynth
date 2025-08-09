"""
Test runner for the Requirement Analysis feature.
"""

import os

import pytest
from pytest_bdd import scenarios

from .steps.test_cli_commands_steps import *

# Import the step definitions
from .steps.test_requirement_analysis_steps import *

# Get the absolute path to the feature file
feature_file = os.path.join(
    os.path.dirname(__file__), "features", "general", "requirement_analysis.feature"
)

# Define the scenarios to test
scenarios(feature_file)
