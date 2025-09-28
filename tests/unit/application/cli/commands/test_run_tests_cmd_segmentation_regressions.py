"""Regression coverage for segmented ``devsynth run-tests`` invocations."""

from __future__ import annotations

import os

import pytest
from typer.testing import CliRunner

from devsynth.testing import run_tests as run_tests_module
from tests.unit.application.cli.commands.helpers import (
    SEGMENTATION_FAILURE_TIPS,
    build_minimal_cli_app,
)


@pytest.mark.fast
def test_segmented_cli_failure_emits_tips_and_reinjection(monkeypatch, tmp_path) -> None:
    """Segmented runs surface remediation tips and reinjection notices once."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "")

    app, cli_module = build_minimal_cli_app(monkeypatch)

    cov_calls: list[dict[str, str]] = []
    bdd_calls: list[dict[str, str]] = []

    def cov_wrapper(env: dict[str, str]) -> bool:
        cov_calls.append(env.copy())
        return run_tests_module.ensure_pytest_cov_plugin_env(env)

    def bdd_wrapper(env: dict[str, str]) -> bool:
        bdd_calls.append(env.copy())
        return run_tests_module.ensure_pytest_bdd_plugin_env(env)

    monkeypatch.setattr(cli_module, "ensure_pytest_cov_plugin_env", cov_wrapper)
    monkeypatch.setattr(cli_module, "ensure_pytest_bdd_plugin_env", bdd_wrapper)
    monkeypatch.setattr(
        cli_module,
        "run_tests",
        lambda *_, **__: (False, SEGMENTATION_FAILURE_TIPS),
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--target",
            "unit-tests",
            "--speed",
            "fast",
            "--segment",
            "--segment-size",
            "2",
            "--no-parallel",
        ],
        prog_name="run-tests",
    )

    assert result.exit_code == 1
    assert "Tests failed" in result.stdout
    assert "Pytest exited with code 1" in result.stdout
    assert "Segment large suites to localize failures" in result.stdout
    assert "Re-run failing segments with --verbose for more detail" in result.stdout

    cov_notice = "-p pytest_cov appended to PYTEST_ADDOPTS because plugin autoloading is disabled"
    bdd_notice = "-p pytest_bdd.plugin appended to PYTEST_ADDOPTS because plugin autoloading is disabled"
    assert result.stdout.count(cov_notice) == 1
    assert result.stdout.count(bdd_notice) == 1

    assert len(cov_calls) == 1
    assert len(bdd_calls) == 1
    assert "-p pytest_cov" in os.environ["PYTEST_ADDOPTS"]
    assert "pytest_bdd" in os.environ["PYTEST_ADDOPTS"]
