"""Typer CLI coverage enforcement tests for ``devsynth run-tests``."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.unit.application.cli.commands.helpers import build_minimal_cli_app


@pytest.mark.fast
def test_cli_reports_coverage_artifacts_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Successful CLI run emits artifact locations after enforcing thresholds."""

    monkeypatch.chdir(tmp_path)

    app, cli_module = build_minimal_cli_app(monkeypatch)

    html_dir = tmp_path / "htmlcov"
    html_dir.mkdir()
    html_index = html_dir / "index.html"
    html_index.write_text("<html>coverage</html>")

    json_path = tmp_path / "test_reports" / "coverage.json"
    json_path.parent.mkdir()
    json_path.write_text("{}")

    monkeypatch.setattr(cli_module, "COVERAGE_HTML_DIR", html_dir)
    monkeypatch.setattr(cli_module, "COVERAGE_JSON_PATH", json_path)

    monkeypatch.setattr(cli_module, "run_tests", lambda *_, **__: (True, "pytest ok"))
    monkeypatch.setattr(
        cli_module, "_coverage_instrumentation_status", lambda: (True, None)
    )

    artifact_calls: list[None] = []

    def _coverage_artifact_status_stub() -> tuple[bool, str | None]:
        artifact_calls.append(None)
        return True, None

    monkeypatch.setattr(
        cli_module, "coverage_artifacts_status", _coverage_artifact_status_stub
    )

    monkeypatch.setattr(
        cli_module,
        "enforce_coverage_threshold",
        lambda exit_on_failure=False: 91.2,
    )
    monkeypatch.setattr(cli_module, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["--target", "unit-tests", "--speed", "fast", "--report"],
        prog_name="run-tests",
    )

    assert result.exit_code == 0
    assert "Coverage 91.20% meets the 70% threshold" in result.stdout
    assert str(html_index.resolve()) in result.stdout
    assert str(json_path.resolve()) in result.stdout
    assert artifact_calls, "coverage_artifacts_status should be evaluated"


@pytest.mark.fast
def test_cli_exits_when_coverage_artifacts_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing coverage artifacts trigger an exit with remediation guidance."""

    monkeypatch.chdir(tmp_path)

    app, cli_module = build_minimal_cli_app(monkeypatch)

    monkeypatch.setattr(cli_module, "run_tests", lambda *_, **__: (True, ""))
    monkeypatch.setattr(
        cli_module, "_coverage_instrumentation_status", lambda: (True, None)
    )
    monkeypatch.setattr(cli_module, "enforce_coverage_threshold", lambda **_: 80.0)
    monkeypatch.setattr(
        cli_module,
        "coverage_artifacts_status",
        lambda: (False, "coverage.json missing"),
    )
    monkeypatch.setattr(
        cli_module,
        "_emit_coverage_artifact_messages",
        lambda _: (_ for _ in ()).throw(
            AssertionError("Coverage messaging should not run when artifacts fail")
        ),
    )
    monkeypatch.setattr(cli_module, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["--target", "unit-tests", "--speed", "fast"],
        prog_name="run-tests",
    )

    assert result.exit_code == 1
    assert "Coverage artifacts missing or empty" in result.stdout
    assert "coverage.json missing" in result.stdout
    assert "Ensure pytest-cov is active for this session" in result.stdout


@pytest.mark.fast
def test_cli_surfaces_threshold_runtime_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Runtime errors from threshold enforcement bubble up through the CLI."""

    monkeypatch.chdir(tmp_path)

    app, cli_module = build_minimal_cli_app(monkeypatch)

    monkeypatch.setattr(cli_module, "run_tests", lambda *_, **__: (True, ""))
    monkeypatch.setattr(
        cli_module, "_coverage_instrumentation_status", lambda: (True, None)
    )
    monkeypatch.setattr(cli_module, "coverage_artifacts_status", lambda: (True, None))
    monkeypatch.setattr(
        cli_module,
        "enforce_coverage_threshold",
        lambda exit_on_failure=False: (_ for _ in ()).throw(
            RuntimeError("Coverage 62.5% below threshold")
        ),
    )
    monkeypatch.setattr(
        cli_module,
        "_emit_coverage_artifact_messages",
        lambda _: (_ for _ in ()).throw(
            AssertionError("Coverage messaging should not run on failure")
        ),
    )
    monkeypatch.setattr(cli_module, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["--target", "unit-tests", "--speed", "fast"],
        prog_name="run-tests",
    )

    assert result.exit_code == 1
    assert "Coverage 62.5% below threshold" in result.stdout
