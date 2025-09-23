"""Additional tests for the ``run-tests`` CLI command to improve coverage.

Covers:
- Inventory-only mode JSON export and bypass of run_tests
- Invalid --target validation error
- --marker forwarding to run_tests extra_marker

ReqIDs: FR-22 (CLI behavior), C3 (coverage targeting)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module
from devsynth.interface.cli import CLIUXBridge


@pytest.fixture(autouse=True)
def _patch_coverage_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "enforce_coverage_threshold", lambda *a, **k: 100.0)
    monkeypatch.setattr(module, "coverage_artifacts_status", lambda: (True, None))


@pytest.mark.fast
def test_inventory_mode_exports_json_and_skips_run(monkeypatch, tmp_path):
    """--inventory should write a JSON file and not call run_tests.

    Ensures no subprocess run is performed and output path exists.
    """
    # Ensure clean env
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    runner = CliRunner()
    with (
        patch("devsynth.application.cli.commands.run_tests_cmd.run_tests") as mock_run,
        patch(
            "devsynth.application.cli.commands.run_tests_cmd.collect_tests_with_cache",
            return_value=["tests/unit/sample_test.py::test_example"],
        ),
    ):
        app = build_app()
        result = runner.invoke(
            app,
            [
                "run-tests",
                "--inventory",
            ],
        )

    assert result.exit_code == 0
    # Ensure run_tests was never called in inventory mode
    mock_run.assert_not_called()

    out = Path("test_reports/test_inventory.json")
    assert out.exists(), "Inventory JSON should be written"
    data = json.loads(out.read_text())
    assert "generated_at" in data and "targets" in data
    # Verify structure for at least one entry
    assert "all-tests" in data["targets"]
    assert set(data["targets"]["all-tests"].keys()) == {"fast", "medium", "slow"}


@pytest.mark.fast
def test_inventory_mode_handles_collection_failures(monkeypatch, tmp_path):
    """Collection failures fall back to empty lists in the inventory export."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    def fake_collect(target: str, speed: str | None = None) -> list[str]:
        if target == "integration-tests" and speed == "medium":
            raise RuntimeError("collection failed")
        entry = [f"{target}/{speed or 'all'}::test_example"]
        return entry

    runner = CliRunner()
    app = build_app()
    with (
        patch.object(module, "collect_tests_with_cache", side_effect=fake_collect),
        patch.object(module, "run_tests") as mock_run,
    ):
        result = runner.invoke(app, ["run-tests", "--inventory"])

    assert result.exit_code == 0

    mock_run.assert_not_called()

    payload = json.loads(Path("test_reports/test_inventory.json").read_text())
    integration_medium = payload["targets"]["integration-tests"]["medium"]
    assert integration_medium == []
    # Ensure healthy targets still record their collected ids
    assert payload["targets"]["integration-tests"]["fast"]


@pytest.mark.fast
def test_invalid_target_exits_with_help_text():
    """Invalid --target should exit with code 2 and provide guidance."""
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(
        app,
        [
            "run-tests",
            "--target",
            "not-a-valid-target",
        ],
    )
    assert result.exit_code == 2
    assert "Invalid --target value" in result.output
    assert (
        "Allowed: all-tests|unit-tests|integration-tests|behavior-tests"
        in result.output
    )
    assert "docs/user_guides/cli_command_reference.md" in result.output


@pytest.mark.fast
def test_marker_option_is_forwarded_to_runner():
    """-m/--marker should be forwarded via extra_marker to run_tests."""
    runner = CliRunner()
    with patch(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        return_value=(True, ""),
    ) as mock_run:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "run-tests",
                "--target",
                "unit-tests",
                "-m",
                "requires_resource('lmstudio')",
            ],
        )

    assert result.exit_code == 0
    # Validate extra_marker was provided via kwargs
    _, kwargs = mock_run.call_args
    assert kwargs.get("extra_marker") == "requires_resource('lmstudio')"
