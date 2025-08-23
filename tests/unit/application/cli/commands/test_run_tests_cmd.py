"""Tests for the ``run-tests`` CLI command."""

import importlib
import os
import sys
import typing
from unittest.mock import patch

import click
import pytest
import typer
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import run_tests_cmd as module

pytestmark = pytest.mark.fast


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    """Allow Typer to handle custom parameter types used in the CLI."""

    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {module.UXBridge, typer.models.Context, typing.Any}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if origin in {module.UXBridge, typer.models.Context, typing.Any}:
            return click.STRING
        try:
            return orig(annotation=annotation, parameter_info=parameter_info)
        except RuntimeError:
            return click.STRING

    monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)


class DummyBridge:
    """Simple bridge stub used for direct invocation tests."""

    def print(self, *args, **kwargs):  # pragma: no cover - trivial
        pass


def test_run_tests_cmd_invokes_runner() -> None:
    """run_tests_cmd should call the underlying ``run_tests`` helper.

    ReqID: FR-22"""

    with patch.object(module, "run_tests", return_value=(True, "ok")) as mock_run:
        module.run_tests_cmd(target="unit-tests", speeds=["fast"], bridge=DummyBridge())
        mock_run.assert_called_once()


def test_run_tests_cmd_nonzero_exit() -> None:
    """run_tests_cmd exits with code 1 when tests fail.

    ReqID: FR-22"""

    with patch.object(module, "run_tests", return_value=(False, "bad")):
        with pytest.raises(module.typer.Exit) as exc:
            module.run_tests_cmd(target="unit-tests", bridge=DummyBridge())
        assert exc.value.exit_code == 1


def test_run_tests_cmd_sets_optional_provider_guard(monkeypatch) -> None:
    """Unset provider env vars default to skipping optional resources.

    ReqID: FR-22"""

    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    monkeypatch.delitem(sys.modules, "lmstudio", raising=False)
    with patch.object(module, "run_tests", return_value=(True, "")):
        module.run_tests_cmd(target="unit-tests", bridge=DummyBridge())
    assert os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE") == "false"


def test_run_tests_cli_full_invocation() -> None:
    """Full CLI invocation delegates to ``run_tests`` and succeeds.

    ReqID: FR-22"""

    runner = CliRunner()
    with patch(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        return_value=(True, ""),
    ) as mock_run:
        app = build_app()
        result = runner.invoke(
            app,
            ["run-tests", "--target", "unit-tests", "--speed", "fast", "--verbose"],
        )

        assert result.exit_code == 0
        mock_run.assert_called_once_with(
            "unit-tests",
            ["fast"],
            True,  # verbose
            False,  # report
            True,  # parallel
            False,  # segment
            50,  # segment_size
            None,  # maxfail
        )
        assert "Tests completed successfully" in result.output


def test_run_tests_cli_help() -> None:
    """The ``--help`` flag should render without Typer runtime errors.

    ReqID: FR-22"""

    runner = CliRunner()
    app = typer.Typer()
    app.command(name="run-tests")(module.run_tests_cmd)
    result = runner.invoke(app, ["run-tests", "--help"])

    assert result.exit_code == 0
    assert "Run DevSynth test suites." in result.output


def test_run_tests_cli_maxfail_option() -> None:
    """``--maxfail`` forwards the value to the runner.

    ReqID: FR-22"""

    runner = CliRunner()
    with patch(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        return_value=(True, ""),
    ) as mock_run:
        app = build_app()
        result = runner.invoke(
            app,
            ["run-tests", "--target", "unit-tests", "--maxfail", "2"],
        )

        assert result.exit_code == 0
        mock_run.assert_called_once_with(
            "unit-tests",
            None,
            False,
            False,
            True,
            False,
            50,
            2,
        )


def test_run_tests_cli_fast_without_optional_providers(monkeypatch) -> None:
    """CLI fast run should succeed when optional providers are absent.

    ReqID: FR-22"""

    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)

    real_find_spec = importlib.util.find_spec

    def missing_spec(name):
        if name == "lmstudio":
            return None
        return real_find_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", missing_spec)

    runner = CliRunner()
    with patch(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        return_value=(True, ""),
    ) as mock_run:
        app = build_app()
        result = runner.invoke(app, ["run-tests", "--speed", "fast"])

    assert result.exit_code == 0
    assert os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE") == "false"
    mock_run.assert_called_once()
