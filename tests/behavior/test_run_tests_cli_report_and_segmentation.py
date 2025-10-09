"""Behavior tests for run-tests CLI reporting and segmentation.

SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullets for --report, --segment, optional providers, and coverage enforcement.

ReqID: FR-22 | Matrix items 4.2.2, 4.2.3, 4.2.5, 4.2.6
"""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_run_tests_cli_steps import *  # noqa: F401,F403

FEATURE_FILE = feature_path(
    __file__, "general", "run_tests_cli_report_and_segmentation.feature"
)


pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

scenarios(FEATURE_FILE)
