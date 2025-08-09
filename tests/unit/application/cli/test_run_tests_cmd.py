"""Tests for run-tests CLI feature flag handling."""

from unittest.mock import patch

from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module


def test_parse_feature_options() -> None:
    """`_parse_feature_options` converts option values to booleans."""

    result = module._parse_feature_options(["a", "b=false", "c=1"])
    assert result == {"a": True, "b": False, "c": True}


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
