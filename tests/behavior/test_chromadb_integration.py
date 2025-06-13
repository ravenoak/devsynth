"""
Test runner for the ChromaDB Integration feature.
"""
import os
import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.requires_resource("chromadb")

# Import step definitions
from .steps.cli_commands_steps import *
from .steps.chromadb_steps import *

# Define the feature file to test
# Use a function to delay the scenarios loading until test execution
def test_chromadb_scenarios():
    scenarios('features/chromadb_integration.feature')
