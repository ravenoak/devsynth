"""
Test runner for the ChromaDB Integration feature.
"""
import os
import pytest
from pytest_bdd import scenarios

# Import step definitions
from steps.cli_commands_steps import *
from steps.chromadb_steps import *

# Define the feature file to test
scenarios('chromadb_integration.feature')
