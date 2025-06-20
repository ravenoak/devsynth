"""
Test runner for the Enhanced ChromaDB Integration feature.
"""
import os
import pytest

chromadb_enabled = os.environ.get("ENABLE_CHROMADB", "false").lower() not in {
    "0",
    "false",
    "no",
}
if not chromadb_enabled:
    pytest.skip("ChromaDB feature not enabled", allow_module_level=True)
from pytest_bdd import scenarios

pytestmark = pytest.mark.requires_resource("chromadb")

# Import step definitions
from .steps.cli_commands_steps import *
from .steps.chromadb_steps import *
from .steps.enhanced_chromadb_steps import *

# Define the feature file to test
# Use a function to delay the scenarios loading until test execution
def test_enhanced_chromadb_scenarios():
    scenarios('features/enhanced_chromadb_integration.feature')
