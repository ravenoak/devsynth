"""Behavior tests for the run-tests CLI command."""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_run_tests_cli_steps import *  # noqa: F401,F403

FEATURE_FILE = feature_path(__file__, "general", "run_tests_cli.feature")


pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

scenarios(FEATURE_FILE)
