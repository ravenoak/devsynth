"""Additional option parsing tests for run-tests CLI. ReqID: QA-07."""

# Coverage: src/devsynth/application/cli/commands/run_tests_cmd.py:204-420

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
    with patch("devsynth.testing.run_tests.run_tests", return_value=(True, "")) as mock_run:
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
    with patch("devsynth.testing.run_tests.run_tests", return_value=(True, "")) as mock_run:
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
    with patch("devsynth.testing.run_tests.run_tests", return_value=(True, "")) as mock_run:
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


@pytest.mark.medium
def test_cli_rejects_invalid_target() -> None:
    """run_tests_cmd target validation prints guidance before exiting (lines 214-229)."""

    runner = CliRunner()
    app = build_app()

    with (
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch("devsynth.observability.metrics.increment_counter", return_value=None),
        patch("devsynth.testing.run_tests.run_tests") as mock_run,
    ):
        result = runner.invoke(app, ["run-tests", "--target", "invalid"])

    assert result.exit_code == 2
    assert "Invalid --target value" in result.output
    mock_run.assert_not_called()


@pytest.mark.medium
def test_cli_rejects_invalid_speed() -> None:
    """Invalid --speed entries surface remediation text (run_tests_cmd.py:231-244)."""

    runner = CliRunner()
    app = build_app()

    with (
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch("devsynth.observability.metrics.increment_counter", return_value=None),
        patch("devsynth.testing.run_tests.run_tests") as mock_run,
    ):
        result = runner.invoke(app, ["run-tests", "--speed", "warp"])

    assert result.exit_code == 2
    assert "Invalid --speed value(s):" in result.output
    mock_run.assert_not_called()


@pytest.mark.medium
def test_cli_reports_disabled_coverage() -> None:
    """Disabled coverage flows emit remediation and exit 1 (run_tests_cmd.py:312-356)."""

    runner = CliRunner()
    app = build_app()

    with (
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch("devsynth.observability.metrics.increment_counter", return_value=None),
        patch("devsynth.application.cli.commands.run_tests_cmd._emit_coverage_artifact_messages", return_value=None),
        patch("devsynth.testing.run_tests.run_tests", return_value=(True, "Done")) as mock_run,
        patch(
            "devsynth.application.cli.commands.run_tests_cmd._coverage_instrumentation_status",
            return_value=(
                False,
                "pytest plugin autoload disabled without -p pytest_cov",
            ),
        ),
        patch("devsynth.testing.run_tests.coverage_artifacts_status") as mock_artifacts,
        patch("devsynth.testing.run_tests.enforce_coverage_threshold") as mock_enforce,
    ):
        result = runner.invoke(app, ["run-tests"])

    assert result.exit_code == 1
    assert "Coverage enforcement skipped" in result.output
    assert "Unset PYTEST_DISABLE_PLUGIN_AUTOLOAD" in result.output
    mock_run.assert_called_once()
    mock_artifacts.assert_not_called()
    mock_enforce.assert_not_called()
