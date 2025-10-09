"""Behavior tests that cover CLI segmentation fallbacks."""

import pytest

pytest.importorskip("pytest_bdd")
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_run_tests_cli_steps import *  # noqa: F401,F403

FEATURE_FILE = feature_path(__file__, "general", "run_tests_from_the_cli.feature")

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

scenarios(FEATURE_FILE)
