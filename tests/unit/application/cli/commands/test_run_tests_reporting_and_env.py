"""Additional targeted tests for run-tests CLI covering reporting and env overrides.

ReqID: FR-22 (CLI behavior) | Cov: 6.2 (targeted tests for CLI/provider)
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module


@pytest.fixture(autouse=True)
def _patch_coverage_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "enforce_coverage_threshold", lambda *a, **k: 100.0)


class _DummyBridge:
    def print(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - trivial
        pass


@pytest.mark.fast
def test_run_tests_cli_report_option_forwards_true() -> None:
    """--report should be forwarded as True to the underlying run_tests helper.

    This ensures HTML report generation wiring is intact at the CLI layer.
    """

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
                "--speed",
                "fast",
                "--report",
            ],
        )

    assert result.exit_code == 0
    # Args: target, speeds, verbose, report, parallel, segment, segment_size, maxfail
    mock_run.assert_called_once_with(
        "unit-tests",
        ["fast"],
        False,
        True,  # report must be True
        True,
        False,
        50,
        None,
    )


@pytest.mark.fast
def test_run_tests_cmd_respects_explicit_provider_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When provider env vars are explicitly set, CLI must not override them.

    - DEVSYNTH_PROVIDER=openai
    - DEVSYNTH_OFFLINE=false
    - DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
    """

    # Pre-set explicit values that should be respected
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")

    with patch.object(module, "run_tests", return_value=(True, "")):
        module.run_tests_cmd(
            target="unit-tests", speeds=["fast"], bridge=_DummyBridge()
        )

    # Ensure values were not force-overwritten by test defaults
    assert os.environ.get("DEVSYNTH_PROVIDER") == "openai"
    assert os.environ.get("DEVSYNTH_OFFLINE") == "false"
    # Availability should remain true since it was explicitly set before
    assert os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE") == "true"
