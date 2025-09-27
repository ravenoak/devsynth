"""Typer-based CLI regression tests for ``devsynth run-tests``."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from devsynth.testing import run_tests as run_tests_module
from tests.unit.application.cli.commands.helpers import build_minimal_cli_app


@pytest.mark.fast
def test_cli_segmented_run_injects_plugins_and_emits_failure_tips(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Segmented runs via Typer surface troubleshooting tips and reinject plugins."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    node_ids = [
        "tests/unit/test_alpha.py::test_one",
        "tests/unit/test_beta.py::test_two",
        "tests/unit/test_gamma.py::test_three",
    ]

    monkeypatch.setattr(
        run_tests_module,
        "collect_tests_with_cache",
        lambda target, speed: list(node_ids),
    )

    monkeypatch.setattr(run_tests_module, "_reset_coverage_artifacts", lambda: None)

    ensure_calls: list[None] = []
    monkeypatch.setattr(
        run_tests_module,
        "_ensure_coverage_artifacts",
        lambda: ensure_calls.append(None),
    )

    popen_calls: list[dict[str, Any]] = []

    class DummyProcess:
        def __init__(self, cmd: list[str], env: dict[str, str], **_: Any) -> None:
            self.cmd = cmd
            self.env = env
            self.index = len(popen_calls)
            # Fail the final batch to trigger troubleshooting tips
            self.returncode = 0 if self.index < len(node_ids) - 1 else 1
            popen_calls.append({"cmd": cmd, "env": env, "index": self.index})

        def communicate(self) -> tuple[str, str]:
            return (f"segment-{self.index + 1} output\n", "")

    monkeypatch.setattr(run_tests_module.subprocess, "Popen", DummyProcess)

    runner = CliRunner()
    app, _ = build_minimal_cli_app(monkeypatch)
    result = runner.invoke(
        app,
        [
            "--target",
            "unit-tests",
            "--speed",
            "fast",
            "--segment",
            "--segment-size",
            "1",
            "--no-parallel",
        ],
        prog_name="run-tests",
    )

    assert result.exit_code == 1
    assert len(popen_calls) == len(node_ids)
    assert ensure_calls, "_ensure_coverage_artifacts should run after segmentation"
    # Failure tips should surface from devsynth.testing.run_tests._failure_tips
    assert "Pytest exited with code 1" in result.stdout
    assert "- Segment large suites to localize failures" in result.stdout
    # Both pytest-cov and pytest-bdd must be reinjected into PYTEST_ADDOPTS
    for call in popen_calls:
        addopts = call["env"].get("PYTEST_ADDOPTS", "")
        assert "-p pytest_cov" in addopts
        assert "pytest_bdd" in addopts


@pytest.mark.fast
def test_cli_inventory_mode_exports_json_via_typer(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Inventory-only mode collects all targets and writes JSON via the CLI."""

    monkeypatch.chdir(tmp_path)

    calls: list[tuple[str, str | None]] = []

    def fake_collect(target: str, speed: str | None) -> list[str]:
        calls.append((target, speed))
        # Encode target/speed in the node id so assertions are deterministic
        suffix = speed or "all"
        return [f"{target}::{suffix}::test_case"]

    app, cli_module = build_minimal_cli_app(monkeypatch)
    monkeypatch.setattr(cli_module, "collect_tests_with_cache", fake_collect)

    runner = CliRunner()
    result = runner.invoke(app, ["--inventory"], prog_name="run-tests")

    assert result.exit_code == 0
    assert "Test inventory exported to" in result.stdout
    assert len(calls) == 12  # 4 targets × 3 speed buckets

    inventory_path = tmp_path / "test_reports" / "test_inventory.json"
    payload = json.loads(inventory_path.read_text())
    assert "generated_at" in payload
    assert set(payload["targets"].keys()) == {
        "all-tests",
        "unit-tests",
        "integration-tests",
        "behavior-tests",
    }
    assert payload["targets"]["unit-tests"]["fast"] == [
        "unit-tests::fast::test_case"
    ]


@pytest.mark.fast
def test_cli_enforces_coverage_threshold_via_cli_runner(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Successful Typer invocation enforces coverage thresholds and emits tips."""

    monkeypatch.chdir(tmp_path)

    app, cli_module = build_minimal_cli_app(monkeypatch)

    runner = CliRunner()

    monkeypatch.setattr(cli_module, "run_tests", lambda *args, **kwargs: (True, "ok"))

    status_calls: list[None] = []
    monkeypatch.setattr(
        cli_module,
        "_coverage_instrumentation_status",
        lambda: status_calls.append(None) or (True, None),
    )

    artifact_calls: list[None] = []

    def _coverage_artifacts_status_stub() -> tuple[bool, str | None]:
        artifact_calls.append(None)
        return True, None

    monkeypatch.setattr(
        cli_module,
        "coverage_artifacts_status",
        _coverage_artifacts_status_stub,
    )

    threshold_calls: list[bool] = []
    threshold_value = 87.5
    monkeypatch.setattr(
        cli_module,
        "enforce_coverage_threshold",
        lambda exit_on_failure=False: threshold_calls.append(exit_on_failure)
        or threshold_value,
    )

    emit_calls: list[object] = []
    monkeypatch.setattr(
        cli_module,
        "_emit_coverage_artifact_messages",
        lambda bridge: emit_calls.append(bridge),
    )

    monkeypatch.setattr(
        cli_module, "ensure_pytest_cov_plugin_env", lambda env: False
    )
    monkeypatch.setattr(
        cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False
    )

    result = runner.invoke(
        app,
        ["--target", "unit-tests", "--speed", "fast", "--report"],
        prog_name="run-tests",
    )

    assert result.exit_code == 0
    assert "Tests completed successfully" in result.stdout
    expected_notice = "Coverage 87.50% meets the 70% threshold"
    assert expected_notice in result.stdout
    assert artifact_calls, "coverage_artifacts_status should run in coverage mode"
    assert threshold_calls == [False]
    assert emit_calls, "_emit_coverage_artifact_messages should be invoked"


@pytest.mark.fast
def test_cli_exits_when_pytest_cov_disabled_via_autoload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Typer run surfaces remediation tips when pytest-cov is disabled."""

    app, cli_module = build_minimal_cli_app(monkeypatch)

    runner = CliRunner()

    monkeypatch.setattr(cli_module, "run_tests", lambda *args, **kwargs: (True, ""))

    reason = "pytest plugin autoload disabled without -p pytest_cov"
    monkeypatch.setattr(
        cli_module,
        "_coverage_instrumentation_status",
        lambda: (False, reason),
    )

    monkeypatch.setattr(
        cli_module,
        "enforce_coverage_threshold",
        lambda exit_on_failure=False: (_ for _ in ()).throw(
            AssertionError("Threshold enforcement should be skipped")
        ),
    )

    monkeypatch.setattr(
        cli_module,
        "coverage_artifacts_status",
        lambda: (_ for _ in ()).throw(
            AssertionError("Artifacts should not be inspected when coverage disabled")
        ),
    )

    monkeypatch.setattr(
        cli_module, "ensure_pytest_cov_plugin_env", lambda env: False
    )
    monkeypatch.setattr(
        cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False
    )

    result = runner.invoke(
        app,
        ["--target", "unit-tests", "--speed", "fast"],
        prog_name="run-tests",
    )

    assert result.exit_code == 1
    assert "Coverage enforcement skipped" in result.stdout
    assert "pytest-cov was disabled" in result.stdout
    assert "Unset PYTEST_DISABLE_PLUGIN_AUTOLOAD=1" in result.stdout
