"""
Test runner for the ChromaDB Integration feature.
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


def test_chromadb_scenarios_succeeds():
    """Test that chromadb scenarios succeeds.

ReqID: N/A"""
    scenarios('features/chromadb_integration.feature')
