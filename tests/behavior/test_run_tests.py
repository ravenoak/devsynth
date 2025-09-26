"""Behavior tests for the run-tests command."""

import os

import pytest
from pytest_bdd import scenarios

# Ensure BDD step definitions are loaded
from tests.behavior.steps import test_run_tests_steps  # noqa: F401

pytest_plugins = [
    "tests.behavior.steps.test_run_tests_steps",
]

FEATURE_FILE = os.path.join(
    os.path.dirname(__file__), "features", "general", "run_tests.feature"
)

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

# Apply speed marker at function level by wrapping scenarios in a generated test
scenarios(FEATURE_FILE)

# Note: pytest-bdd generates test functions automatically.
# Speed markers for behavior tests are applied centrally in tests/behavior/conftest.py
# to ensure exactly one function-level marker per scenario.
