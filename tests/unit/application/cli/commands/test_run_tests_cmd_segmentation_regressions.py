"""Regression coverage for segmented ``devsynth run-tests`` invocations."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from devsynth.testing import run_tests as run_tests_module
from tests.unit.application.cli.commands.helpers import (
    SEGMENTATION_FAILURE_TIPS,
    build_minimal_cli_app,
)


def _build_batch_output(label: str, error: Exception) -> str:
    """Compose deterministic stderr for simulated failing batches."""

    return f"[batch {label}] {error}\n{SEGMENTATION_FAILURE_TIPS}"


@pytest.mark.fast
def test_segmented_cli_failure_emits_tips_and_reinjection(
    monkeypatch, tmp_path
) -> None:
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

    assert isinstance(result.exception, SystemExit)
    assert result.exit_code == 1
    assert result.exception.code == 1
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


@pytest.mark.fast
@pytest.mark.parametrize(
    "failed_batches",
    [
        pytest.param(["one"], id="single-batch"),
        pytest.param(["one", "two", "three"], id="multiple-batches"),
    ],
)
def test_segmented_cli_failure_repeats_banner_per_batch_and_aggregate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failed_batches: list[str],
) -> None:
    """Remediation banners surface once per failed segment and aggregate."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "")

    app, cli_module = build_minimal_cli_app(monkeypatch)

    observed_batches: list[str] = []

    def raising_segment(label: str) -> None:
        observed_batches.append(label)
        raise RuntimeError(f"segment {label} crashed")

    monkeypatch.setattr(
        run_tests_module,
        "_segment_batches",
        raising_segment,
        raising=False,
    )

    received_kwargs: dict[str, object] = {}

    def fake_run_tests(*_: object, **kwargs: object) -> tuple[bool, str]:
        received_kwargs.update(kwargs)
        batch_outputs: list[str] = []
        for index, batch in enumerate(failed_batches, start=1):
            try:
                run_tests_module._segment_batches(batch)  # type: ignore[attr-defined]
            except RuntimeError as exc:  # pragma: no cover - exercised via test logic
                batch_outputs.append(_build_batch_output(str(index), exc))
        batch_outputs.append(
            "Aggregate segmentation failure\n" + SEGMENTATION_FAILURE_TIPS
        )
        return False, "\n".join(batch_outputs)

    monkeypatch.setattr(cli_module, "run_tests", fake_run_tests)
    monkeypatch.setattr(
        cli_module, "_coverage_instrumentation_status", lambda: (True, None)
    )
    monkeypatch.setattr(cli_module, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--segment",
            "--segment-size",
            "2",
            "--speed",
            "fast",
            "--target",
            "unit-tests",
        ],
        prog_name="run-tests",
    )

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert result.exception.code == 1
    assert received_kwargs.get("segment") is True
    assert received_kwargs.get("segment_size") == 2
    assert observed_batches == failed_batches

    remediation_count = result.stdout.count("Segment large suites to localize failures")
    assert remediation_count == len(failed_batches) + 1
    assert result.stdout.count("Aggregate segmentation failure") == 1
