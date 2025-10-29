"""Tests for run-tests CLI feature flag handling."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module


@pytest.mark.fast
def test_parse_feature_options() -> None:
    """`_parse_feature_options` converts option values to booleans."""

    result = module._parse_feature_options(["a", "b=false", "c=1"])
    assert result == {"a": True, "b": False, "c": True}


@pytest.mark.fast
def test_cli_accepts_feature_flags() -> None:
    """CLI invocation with ``--feature`` delegates to `run_tests`."""

    runner = CliRunner()
    with patch.object(module, "run_tests", return_value=(True, "")) as mock_run:
        app = build_app()
        result = runner.invoke(
            app, ["run-tests", "--feature", "foo=true", "--feature", "bar=false"]
        )
        assert result.exit_code == 0
        mock_run.assert_called_once()


@pytest.mark.fast
def test_cli_reports_coverage_percent() -> None:
    """Successful runs print the measured coverage percentage."""

    runner = CliRunner()
    app = build_app()

    with (
        patch.object(module, "run_tests", return_value=(True, "")),
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch.object(module, "_emit_coverage_artifact_messages", return_value=None),
        patch.object(
            module, "enforce_coverage_threshold", return_value=92.5
        ) as mock_enforce,
        patch.object(
            module, "_coverage_instrumentation_status", return_value=(True, None)
        ),
        patch.object(module, "coverage_artifacts_status", return_value=(True, None)),
        patch.object(module, "increment_counter", return_value=None),
    ):
        result = runner.invoke(app, ["run-tests", "--report"])

    assert result.exit_code == 0
    assert "Coverage 92.50% meets the 90% threshold" in result.output
    mock_enforce.assert_called_once()


@pytest.mark.fast
def test_cli_errors_when_plugins_disabled() -> None:
    """CLI fails fast when pytest-cov was disabled by plugin autoload settings."""

    runner = CliRunner()
    app = build_app()

    with (
        patch.object(module, "run_tests", return_value=(True, "")),
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch.object(module, "_emit_coverage_artifact_messages", return_value=None),
        patch.object(module, "enforce_coverage_threshold", return_value=95.0),
        patch.object(
            module,
            "_coverage_instrumentation_status",
            return_value=(
                False,
                "pytest plugin autoload disabled without -p pytest_cov",
            ),
        ),
        patch.object(
            module,
            "coverage_artifacts_status",
            return_value=(False, "Coverage JSON missing at test_reports/coverage.json"),
        ),
        patch.object(module, "increment_counter", return_value=None),
    ):
        result = runner.invoke(app, ["run-tests"])

    assert result.exit_code == 1
    assert "Unset PYTEST_DISABLE_PLUGIN_AUTOLOAD" in result.output


@pytest.mark.fast
def test_cli_errors_when_artifacts_missing() -> None:
    """CLI reports actionable remediation when coverage artifacts are absent."""

    runner = CliRunner()
    app = build_app()

    with (
        patch.object(module, "run_tests", return_value=(True, "")),
        patch("devsynth.application.cli.commands.run_tests_cmd._configure_optional_providers", return_value=None),
        patch.object(module, "_emit_coverage_artifact_messages", return_value=None),
        patch.object(
            module, "enforce_coverage_threshold", return_value=95.0
        ) as mock_enforce,
        patch.object(
            module, "_coverage_instrumentation_status", return_value=(True, None)
        ),
        patch.object(
            module,
            "coverage_artifacts_status",
            return_value=(False, "Coverage JSON missing at test_reports/coverage.json"),
        ),
        patch.object(module, "increment_counter", return_value=None),
    ):
        result = runner.invoke(app, ["run-tests"])

    assert result.exit_code == 1
    assert "Coverage artifacts missing or empty" in result.output
    mock_enforce.assert_not_called()
