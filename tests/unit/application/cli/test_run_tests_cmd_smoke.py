"""Smoke-mode behavior tests for run-tests CLI."""

import os
from typing import Any, cast
from collections.abc import Callable
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module
from tests._typing_utils import ensure_typed_decorator


@pytest.fixture(autouse=True)
def _patch_coverage_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "enforce_coverage_threshold", lambda *a, **k: 100.0)
    monkeypatch.setattr(module, "coverage_artifacts_status", lambda: (True, None))


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
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch.object(module, "_emit_coverage_artifact_messages") as mock_emit,
        patch.object(module, "enforce_coverage_threshold") as mock_enforce,
        patch.object(
            module, "_coverage_instrumentation_status", return_value=(True, None)
        ),
        patch.object(module, "increment_counter", return_value=None),
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
        assert "--cov-fail-under=0" in addopts
        mock_run.assert_called_once()
        mock_enforce.assert_not_called()
        mock_emit.assert_called_once()
        assert "Coverage enforcement skipped in smoke mode" in result.stdout


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
    addopts = os.environ.get("PYTEST_ADDOPTS", "")
    assert "-p pytest_cov" not in addopts
    assert "--cov-fail-under=0" in addopts


@pytest.mark.fast
def test_smoke_mode_cli_imports_fastapi_testclient(monkeypatch) -> None:
    """ReqID: CLI-RT-19c — Smoke CLI guards against FastAPI/Starlette MRO regressions."""

    pytest.importorskip("fastapi")
    pytest.importorskip("fastapi.testclient")
    pytest.importorskip("starlette")

    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    runner = CliRunner()

    def _fake_run_tests(*_args, **_kwargs):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        route = ensure_typed_decorator(
            cast(Callable[[Callable[..., Any]], Any], app.get("/health"))
        )

        @route
        def _health() -> dict[str, str]:
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        return True, "FastAPI TestClient smoke regression guard OK"

    with (
        patch.object(module, "run_tests", side_effect=_fake_run_tests) as mock_run,
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch.object(module, "_emit_coverage_artifact_messages", return_value=None),
        patch.object(module, "enforce_coverage_threshold", return_value=100.0),
        patch.object(
            module, "_coverage_instrumentation_status", return_value=(True, None)
        ),
        patch.object(module, "coverage_artifacts_status", return_value=(True, None)),
        patch.object(module, "increment_counter", return_value=None),
    ):
        app = build_app()
        result = runner.invoke(
            app,
            ["run-tests", "--smoke", "--speed", "fast", "--maxfail", "1"],
        )

    assert result.exit_code == 0
    assert "FastAPI TestClient smoke regression guard OK" in result.stdout
    mock_run.assert_called_once()


@pytest.mark.fast
def test_smoke_mode_skips_coverage_gate_when_instrumented(monkeypatch) -> None:
    """ReqID: CLI-RT-19d — Smoke mode bypasses coverage thresholds even with pytest-cov."""

    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    runner = CliRunner()

    with (
        patch.object(module, "run_tests", return_value=(True, "")) as mock_run,
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch.object(module, "_emit_coverage_artifact_messages") as mock_emit,
        patch.object(
            module,
            "enforce_coverage_threshold",
            side_effect=AssertionError("should not run"),
        ) as mock_enforce,
        patch.object(
            module, "_coverage_instrumentation_status", return_value=(True, None)
        ),
        patch.object(module, "coverage_artifacts_status", return_value=(True, None)),
        patch.object(module, "increment_counter", return_value=None),
    ):
        app = build_app()
        result = runner.invoke(
            app,
            ["run-tests", "--smoke", "--speed", "fast"],
        )

    assert result.exit_code == 0
    assert "Coverage enforcement skipped in smoke mode" in result.stdout
    mock_run.assert_called_once()
    mock_enforce.assert_not_called()
    mock_emit.assert_called_once()
    addopts = os.environ.get("PYTEST_ADDOPTS", "")
    assert "--cov-fail-under=0" in addopts
