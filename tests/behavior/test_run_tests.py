"""Behavior tests for the run-tests command."""

import os

import pytest
from pytest_bdd import scenarios

FEATURE_FILE = os.path.join(
    os.path.dirname(__file__), "features", "general", "run_tests.feature"
)

pytestmark = pytest.mark.requires_resource("cli")

scenarios(FEATURE_FILE)
