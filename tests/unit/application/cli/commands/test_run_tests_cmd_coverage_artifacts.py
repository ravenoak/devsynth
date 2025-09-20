import json
import logging
import os
import runpy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

import coverage
import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.testing import run_tests as run_tests_module


def _install_pytest_stubs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    collect_stdout_sequence: list[str] | None = None,
) -> tuple[list[dict[str, str]], List[List[str]]]:
    """Stub pytest execution and track coverage consolidation calls."""

    popen_envs: list[dict[str, str]] = []
    combine_calls: list[list[str]] = []

    original_combine = coverage.Coverage.combine

    def tracking_combine(
        self: coverage.Coverage,
        data_paths: list[str] | None = None,
        strict: bool = False,
        keep: bool = False,
    ) -> None:
        paths = [str(Path(p)) for p in (data_paths or [])]
        combine_calls.append(paths)
        return original_combine(self, data_paths=data_paths, strict=strict, keep=keep)

    collect_stdout: list[str] | None = None
    if collect_stdout_sequence is not None:
        collect_stdout = list(collect_stdout_sequence)

    def fake_run(*args: Any, **kwargs: Any) -> SimpleNamespace:
        if collect_stdout:
            stdout = collect_stdout.pop(0)
        else:
            stdout = "tests/unit/test_sample.py::test_ok\n"
        return SimpleNamespace(
            returncode=0,
            stdout=stdout,
            stderr="",
        )

    class DummyProcess:
        _counter = 0

        def __init__(self, captured_env: dict[str, str]) -> None:
            self._env = captured_env
            DummyProcess._counter += 1
            self._fragment = Path(f".coverage.fragment-{DummyProcess._counter}")
            self._script = Path(f"fragment_source_{DummyProcess._counter}.py")
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            self._script.write_text(
                "def _instrumented() -> int:\n"
                "    value = 1\n"
                "    return value\n\n"
                "_instrumented()\n"
            )
            cov = coverage.Coverage(data_file=str(self._fragment))
            cov.start()
            runpy.run_path(str(self._script))
            cov.stop()
            cov.save()
            return ("pytest output", "")

    def fake_popen(*args: Any, **kwargs: Any) -> DummyProcess:
        env = dict(kwargs.get("env") or {})
        popen_envs.append(env)
        return DummyProcess(env)

    monkeypatch.setattr(run_tests_module.subprocess, "run", fake_run)
    monkeypatch.setattr(run_tests_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(coverage.Coverage, "combine", tracking_combine)

    return popen_envs, combine_calls


@pytest.mark.fast
def test_smoke_command_generates_coverage_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Smoke profile writes coverage artifacts even with plugin autoload disabled."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    popen_envs, combine_calls = _install_pytest_stubs(monkeypatch)

    runner = CliRunner()
    app = build_app()
    with caplog.at_level(logging.INFO, logger="devsynth.testing.run_tests"):
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
    assert combine_calls, "coverage fragments should be consolidated"
    assert "-p pytest_cov appended" in result.stdout


@pytest.mark.fast
def test_smoke_command_injects_pytest_bdd_plugin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Smoke profile explicitly loads pytest-bdd when plugin autoload is disabled."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    popen_envs, combine_calls = _install_pytest_stubs(monkeypatch)

    runner = CliRunner()
    app = build_app()
    with caplog.at_level(logging.INFO, logger="devsynth.testing.run_tests"):
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
    assert any("-p pytest_bdd.plugin" in env.get("PYTEST_ADDOPTS", "") for env in popen_envs)
    assert any("-p pytest_cov" in env.get("PYTEST_ADDOPTS", "") for env in popen_envs)
    assert combine_calls, "coverage fragments should be consolidated"
    assert "IndexError" not in result.stdout
    assert "-p pytest_bdd.plugin appended" in result.stdout


@pytest.mark.fast
def test_fast_medium_command_generates_coverage_artifacts_with_autoload_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Fast+medium aggregate run preserves coverage artifacts when autoload is disabled."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    popen_envs, combine_calls = _install_pytest_stubs(monkeypatch)

    runner = CliRunner()
    app = build_app()
    with caplog.at_level(logging.INFO, logger="devsynth.testing.run_tests"):
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
        assert "-p pytest_bdd.plugin" in env.get("PYTEST_ADDOPTS", "")
    assert combine_calls and all(calls for calls in combine_calls)
    assert not list(tmp_path.glob(".coverage.fragment-*"))
    assert "-p pytest_cov appended" in result.stdout


@pytest.mark.fast
def test_fast_medium_command_handles_empty_collection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Fallback to marker execution when collection returns no node identifiers."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    popen_envs, combine_calls = _install_pytest_stubs(
        monkeypatch, collect_stdout_sequence=["", ""]
    )

    runner = CliRunner()
    app = build_app()
    with caplog.at_level(logging.INFO, logger="devsynth.testing.run_tests"):
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
        assert "-p pytest_bdd.plugin" in env.get("PYTEST_ADDOPTS", "")
    assert combine_calls and all(calls for calls in combine_calls)
    assert "marker fallback" in caplog.text
