"""
Test runner for the Requirement Analysis feature.
"""
import pytest
from pytest_bdd import scenarios

# Import the step definitions
from .steps.requirement_analysis_steps import *
from .steps.cli_commands_steps import *

# Define the scenarios to test
scenarios('features/requirement_analysis.feature')
