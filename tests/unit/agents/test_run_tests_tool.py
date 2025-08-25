"""Tests for the run_tests_tool."""

from unittest.mock import patch

from devsynth.agents.tools import get_tool_registry, run_tests_tool


def test_run_tests_tool_returns_structure() -> None:
    """run_tests_tool should return a success flag and output string."""
    with patch(
        "devsynth.agents.tools.run_tests", return_value=(True, "ok")
    ) as mock_run:
        result = run_tests_tool(target="unit-tests")
        assert result == {"success": True, "output": "ok"}
        mock_run.assert_called_once()


def test_run_tests_tool_registered() -> None:
    """The tool should be registered in the global registry."""
    registry = get_tool_registry()
    func = registry.get("run_tests")
    assert func is not None
    with patch(
        "devsynth.agents.tools.run_tests", return_value=(True, "ok")
    ) as mock_run:
        func(target="unit-tests")
        mock_run.assert_called_once()
