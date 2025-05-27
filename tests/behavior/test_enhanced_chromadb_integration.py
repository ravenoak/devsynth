"""
Test runner for the Enhanced ChromaDB Integration feature.
"""
import os
import pytest
from pytest_bdd import scenarios

# Import step definitions
from steps.cli_commands_steps import *
from steps.chromadb_steps import *
from steps.enhanced_chromadb_steps import *

# Define the feature file to test
# Use a function to delay the scenarios loading until test execution
def test_enhanced_chromadb_scenarios():
    scenarios('features/enhanced_chromadb_integration.feature')
