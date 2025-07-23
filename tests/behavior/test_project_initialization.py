
"""
Test runner for the Project Initialization feature.
"""
import os
import pytest
from pytest_bdd import scenarios

# Import step definitions
from .steps.cli_commands_steps import *
from .steps.project_init_steps import *

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "general", "project_initialization.feature")

# Define the feature file to test
scenarios(feature_file)
