"""
Root conftest.py to ensure pytest-bdd configuration is properly loaded.
"""

import os
import pytest
from pytest_bdd.utils import CONFIG_STACK

# Set the base directory for feature files and register markers
@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Configure pytest-bdd and register custom markers."""
    # Register the isolation marker
    config.addinivalue_line(
        "markers", "isolation: mark test to run in isolation due to interactions with other tests"
    )

    # Ensure the CONFIG_STACK is initialized
    if not CONFIG_STACK:
        CONFIG_STACK.append(config)

    # Set the base directory for feature files
    features_dir = os.path.join(
        os.path.dirname(__file__), "tests", "behavior", "features"
    )

    # Set the option directly on the config object
    config.option.bdd_features_base_dir = features_dir

    # Also set it as an ini option for backwards compatibility
    config._inicache['bdd_features_base_dir'] = features_dir
