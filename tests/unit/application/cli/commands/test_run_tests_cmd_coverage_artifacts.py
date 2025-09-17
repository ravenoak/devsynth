import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.testing import run_tests as run_tests_module


def _install_pytest_stubs(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Stub pytest execution to simulate coverage artifact generation."""

    html_dir = run_tests_module.COVERAGE_HTML_DIR
    json_path = run_tests_module.COVERAGE_JSON_PATH
    popen_envs: list[dict[str, str]] = []

    def fake_run(*args: Any, **kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout="tests/unit/test_sample.py::test_ok\n",
            stderr="",
        )

    class DummyProcess:
        def __init__(self, captured_env: dict[str, str]) -> None:
            self._env = captured_env
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            Path(".coverage").write_text("coverage data")
            html_dir.mkdir(parents=True, exist_ok=True)
            (html_dir / "index.html").write_text("<html>coverage report</html>")
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(
                json.dumps({"totals": {"percent_covered": 95.0}})
            )
            return ("pytest output", "")

    def fake_popen(*args: Any, **kwargs: Any) -> DummyProcess:
        env = dict(kwargs.get("env") or {})
        popen_envs.append(env)
        return DummyProcess(env)

    monkeypatch.setattr(run_tests_module.subprocess, "run", fake_run)
    monkeypatch.setattr(run_tests_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(run_tests_module, "_ensure_coverage_artifacts", lambda: None)

    return popen_envs


@pytest.mark.fast
def test_smoke_command_generates_coverage_artifacts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Smoke profile writes coverage artifacts even with plugin autoload disabled."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    popen_envs = _install_pytest_stubs(monkeypatch)

    runner = CliRunner()
    app = build_app()
    result = runner.invoke(
        app,
        [
            "run-tests",
            "--smoke",
            "--speed=fast",
            "--no-parallel",
            "--maxfail=1",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".coverage").exists()
    assert (tmp_path / "test_reports" / "coverage.json").exists()
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    assert any("-p pytest_cov" in env.get("PYTEST_ADDOPTS", "") for env in popen_envs)
    assert "Coverage 95.00% meets the 90% threshold" in result.stdout


@pytest.mark.fast
def test_fast_medium_command_generates_coverage_artifacts_with_autoload_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Fast+medium aggregate run preserves coverage artifacts when autoload is disabled."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    popen_envs = _install_pytest_stubs(monkeypatch)

    runner = CliRunner()
    app = build_app()
    result = runner.invoke(
        app,
        [
            "run-tests",
            "--speed=fast",
            "--speed=medium",
            "--no-parallel",
            "--maxfail=1",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".coverage").exists()
    assert (tmp_path / "test_reports" / "coverage.json").exists()
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert len(popen_envs) == 2
    for env in popen_envs:
        assert env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
        assert "-p pytest_cov" in env.get("PYTEST_ADDOPTS", "")
    assert "Coverage 95.00% meets the 90% threshold" in result.stdout
