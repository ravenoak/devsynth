"""
Test runner for the Enhanced ChromaDB Integration feature.
"""

import os

import pytest

from tests.behavior.feature_paths import feature_path

pytest.importorskip("chromadb")

chromadb_enabled = os.environ.get("ENABLE_CHROMADB", "false").lower() not in {
    "0",
    "false",
    "no",
}
if not chromadb_enabled:
    pytest.skip("ChromaDB feature not enabled", allow_module_level=True)
from pytest_bdd import scenarios

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("chromadb"),
]
from .steps.cli_commands_steps import *
from .steps.test_chromadb_steps import *
from .steps.test_enhanced_chromadb_steps import *


def test_enhanced_chromadb_scenarios_succeeds():
    """Test that enhanced chromadb scenarios succeeds.

    ReqID: N/A"""
    scenarios(
        feature_path(__file__, "general", "enhanced_chromadb_integration.feature")
    )
