"""Behavior tests that cover CLI segmentation fallbacks."""

import os

import pytest

pytest.importorskip("pytest_bdd")
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_run_tests_cli_steps import *  # noqa: F401,F403

FEATURE_FILE = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "run_tests_from_the_cli.feature",
)

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

scenarios(FEATURE_FILE)
