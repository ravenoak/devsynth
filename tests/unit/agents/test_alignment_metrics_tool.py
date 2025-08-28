"""Tests for ``alignment_metrics_tool``."""

from types import ModuleType
from unittest.mock import patch

import pytest

from devsynth.agents.tools import alignment_metrics_tool, get_tool_registry


@pytest.mark.fast
def test_alignment_metrics_tool_returns_structure() -> None:
    """alignment_metrics_tool should return success and metrics."""
    align_cmd = ModuleType("align_cmd")
    align_cmd.get_all_files = lambda path: []

    metrics_cmd = ModuleType("alignment_metrics_cmd")
    metrics_cmd.calculate_alignment_coverage = lambda files: {"coverage": 1}
    metrics_cmd.calculate_alignment_issues = lambda files: {"issues": 2}
    metrics_cmd.load_historical_metrics = lambda path: []
    metrics_cmd.save_metrics = lambda metrics, path, hist: None
    metrics_cmd.generate_metrics_report = lambda m, h, o: None

    with (
        patch("devsynth.agents.tools.os.makedirs"),
        patch.dict(
            "sys.modules",
            {
                "devsynth.application": ModuleType("application"),
                "devsynth.application.cli": ModuleType("cli"),
                "devsynth.application.cli.commands": ModuleType("commands"),
                "devsynth.application.cli.commands.align_cmd": align_cmd,
                "devsynth.application.cli.commands.alignment_metrics_cmd": metrics_cmd,
            },
        ),
    ):
        result = alignment_metrics_tool()
        assert result == {"success": True, "metrics": {"coverage": 1, "issues": 2}}


@pytest.mark.fast
def test_alignment_metrics_tool_registered() -> None:
    """The tool should be registered and callable from the registry."""
    registry = get_tool_registry()
    func = registry.get("alignment_metrics")
    assert callable(func)

    align_cmd = ModuleType("align_cmd")
    align_cmd.get_all_files = lambda path: []

    metrics_cmd = ModuleType("alignment_metrics_cmd")
    metrics_cmd.calculate_alignment_coverage = lambda files: {"coverage": 1}
    metrics_cmd.calculate_alignment_issues = lambda files: {"issues": 2}
    metrics_cmd.load_historical_metrics = lambda path: []
    metrics_cmd.save_metrics = lambda metrics, path, hist: None
    metrics_cmd.generate_metrics_report = lambda m, h, o: None

    with (
        patch("devsynth.agents.tools.os.makedirs"),
        patch.dict(
            "sys.modules",
            {
                "devsynth.application": ModuleType("application"),
                "devsynth.application.cli": ModuleType("cli"),
                "devsynth.application.cli.commands": ModuleType("commands"),
                "devsynth.application.cli.commands.align_cmd": align_cmd,
                "devsynth.application.cli.commands.alignment_metrics_cmd": metrics_cmd,
            },
        ),
    ):
        result = func()
        assert result == {"success": True, "metrics": {"coverage": 1, "issues": 2}}
