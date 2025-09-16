"""Smoke-mode behavior tests for run-tests CLI."""

import os
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module


@pytest.fixture(autouse=True)
def _patch_coverage_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "enforce_coverage_threshold", lambda *a, **k: 100.0)


@pytest.mark.fast
def test_smoke_mode_sets_pytest_disable_plugin_autoload_env(monkeypatch) -> None:
    """ReqID: CLI-RT-19 — Smoke mode disables plugin autoload while keeping
    coverage instrumentation."""
    # Ensure env is clean
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    runner = CliRunner()
    with (
        patch.object(module, "run_tests", return_value=(True, "")) as mock_run,
        patch.object(
            module, "enforce_coverage_threshold", return_value=100.0
        ) as mock_enforce,
    ):
        app = build_app()
        result = runner.invoke(app, ["run-tests", "--smoke"])  # defaults to fast
        assert result.exit_code == 0
        # Env should be set by the time run_tests is called; assert current process env
        assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
        addopts = os.environ.get("PYTEST_ADDOPTS", "")
        assert "-p no:xdist" in addopts
        assert "-p pytest_cov" in addopts
        assert "-p no:cov" not in addopts
        mock_run.assert_called_once()
        mock_enforce.assert_called_once()


@pytest.mark.fast
def test_smoke_mode_skips_coverage_gate_when_cov_disabled(monkeypatch) -> None:
    """ReqID: CLI-RT-19b — Smoke mode skips coverage enforcement when
    instrumentation is disabled."""

    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-p no:cov")

    runner = CliRunner()
    with (
        patch.object(module, "run_tests", return_value=(True, "")) as mock_run,
        patch.object(module, "enforce_coverage_threshold") as mock_enforce,
    ):
        app = build_app()
        result = runner.invoke(app, ["run-tests", "--smoke"])  # defaults to fast

    assert result.exit_code == 0
    mock_run.assert_called_once()
    mock_enforce.assert_not_called()
    output = result.stdout
    assert "Coverage enforcement skipped" in output
    assert "-p pytest_cov" not in os.environ.get("PYTEST_ADDOPTS", "")
