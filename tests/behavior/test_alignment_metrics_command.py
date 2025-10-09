"""Behavioral tests for the alignment metrics CLI command."""

from __future__ import annotations

import os

import pytest
from pytest_bdd import scenario

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.test_alignment_metrics_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.requires_resource("cli")]

_FEATURE_FILE = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "alignment_metrics_command.feature",
)


@scenario(_FEATURE_FILE, "Collect metrics successfully")
@pytest.mark.fast
def test_collect_metrics_successfully() -> None:
    """BDD scenario for successful metrics collection."""


@scenario(_FEATURE_FILE, "Handle failure during metrics collection")
@pytest.mark.fast
def test_handle_failure_during_metrics_collection() -> None:
    """BDD scenario for handling metrics collection failures."""
