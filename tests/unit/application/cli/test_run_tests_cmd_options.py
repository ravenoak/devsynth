"""Additional option parsing tests for run-tests CLI. ReqID: QA-07"""

import os
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module


@pytest.mark.fast
def test_feature_flags_set_environment(monkeypatch) -> None:
    """--feature name[=bool] should set DEVSYNTH_FEATURE_<NAME> env vars."""
    # Ensure clean env
    monkeypatch.delenv("DEVSYNTH_FEATURE_ALPHA", raising=False)
    monkeypatch.delenv("DEVSYNTH_FEATURE_BETA", raising=False)

    runner = CliRunner()
    with patch.object(module, "run_tests", return_value=(True, "")) as mock_run:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "run-tests",
                "--feature",
                "alpha",
                "--feature",
                "beta=false",
            ],
        )
        assert result.exit_code == 0
        # Env flags should be present and normalized
        assert os.environ.get("DEVSYNTH_FEATURE_ALPHA") == "true"
        assert os.environ.get("DEVSYNTH_FEATURE_BETA") == "false"
        mock_run.assert_called_once()


@pytest.mark.fast
def test_no_parallel_flag_is_passed_to_runner() -> None:
    """--no-parallel should result in parallel=False in run_tests call."""
    runner = CliRunner()
    with patch.object(module, "run_tests", return_value=(True, "")) as mock_run:
        app = build_app()
        result = runner.invoke(app, ["run-tests", "--no-parallel", "--speed", "fast"])
        assert result.exit_code == 0
        # Signature: run_tests(target, speeds, verbose, report, parallel, segment, segment_size, maxfail, **kwargs)
        args, kwargs = mock_run.call_args
        assert args[4] is False  # parallel


@pytest.mark.fast
def test_segment_options_are_propagated() -> None:
    """--segment and --segment-size should be passed through to run_tests."""
    runner = CliRunner()
    with patch.object(module, "run_tests", return_value=(True, "")) as mock_run:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "run-tests",
                "--segment",
                "--segment-size",
                "25",
                "--speed",
                "medium",
            ],
        )
        assert result.exit_code == 0
        args, kwargs = mock_run.call_args
        assert args[5] is True  # segment
        assert args[6] == 25  # segment_size
