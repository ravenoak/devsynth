"""Behavior tests for the run-tests command."""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

# Ensure BDD step definitions are loaded
from tests.behavior.steps import test_run_tests_steps  # noqa: F401

FEATURE_FILE = feature_path(__file__, "general", "run_tests.feature")


pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

# Apply speed marker at function level by wrapping scenarios in a generated test
scenarios(FEATURE_FILE)

# Note: pytest-bdd generates test functions automatically.
# Speed markers for behavior tests are applied centrally in tests/behavior/conftest.py
# to ensure exactly one function-level marker per scenario.
