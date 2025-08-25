"""Tests for feature flag propagation in run-tests CLI."""

import os
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app


@pytest.mark.fast
def test_run_tests_cli_feature_flags_set_env(monkeypatch):
    # Ensure a clean env for the feature vars
    monkeypatch.delenv("DEVSYNTH_FEATURE_EXPERIMENTAL", raising=False)
    monkeypatch.delenv("DEVSYNTH_FEATURE_LOGGING", raising=False)

    runner = CliRunner()
    with patch(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        return_value=(True, ""),
    ):
        app = build_app()
        result = runner.invoke(
            app,
            [
                "run-tests",
                "--target",
                "unit-tests",
                "--feature",
                "experimental",
                "--feature",
                "logging=false",
            ],
        )
    assert result.exit_code == 0
    assert os.environ.get("DEVSYNTH_FEATURE_EXPERIMENTAL") == "true"
    assert os.environ.get("DEVSYNTH_FEATURE_LOGGING") == "false"
