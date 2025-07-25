"""
Test runner for the Enhanced ChromaDB Integration feature.
"""
import os
import pytest
chromadb_enabled = os.environ.get('ENABLE_CHROMADB', 'false').lower() not in {
    '0', 'false', 'no'}
if not chromadb_enabled:
    pytest.skip('ChromaDB feature not enabled', allow_module_level=True)
from pytest_bdd import scenarios
pytestmark = pytest.mark.requires_resource('chromadb')
from .steps.cli_commands_steps import *
from .steps.chromadb_steps import *
from .steps.enhanced_chromadb_steps import *


def test_enhanced_chromadb_scenarios_succeeds():
    """Test that enhanced chromadb scenarios succeeds.

ReqID: N/A"""
    scenarios('features/enhanced_chromadb_integration.feature')
