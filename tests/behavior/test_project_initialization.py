
"""
Test runner for the Project Initialization feature.
"""
import os
import pytest
from pytest_bdd import scenarios

# Import step definitions
from .steps.cli_commands_steps import *
from .steps.project_init_steps import *

# Define the feature file to test
scenarios('features/project_initialization.feature')
