"""Behavior tests for run-tests CLI reporting and segmentation.

ReqID: FR-22 | Matrix items 4.2.2, 4.2.3, 4.2.5, 4.2.6
"""

import os

import pytest
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_run_tests_cli_steps import *  # noqa: F401,F403

FEATURE_FILE = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "run_tests_cli_report_and_segmentation.feature",
)


pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

scenarios(FEATURE_FILE)
