import importlib
import json
import logging
import os
import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, List

import coverage
import pytest
from typer import Typer
from typer.testing import CliRunner

from devsynth.testing import run_tests as run_tests_module


def _load_cli_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load run_tests_cmd with registry stubs to avoid optional deps."""

    alignment_module = ModuleType("alignment_metrics_cmd")

    def _noop_alignment(*args: Any, **kwargs: Any) -> bool:
        return True

    alignment_module.alignment_metrics_cmd = _noop_alignment  # type: ignore[attr-defined]
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.alignment_metrics_cmd",
        alignment_module,
    )

    test_metrics_module = ModuleType("test_metrics_cmd")
    test_metrics_module.test_metrics_cmd = _noop_alignment  # type: ignore[attr-defined]
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.test_metrics_cmd",
        test_metrics_module,
    )

    registry_module = ModuleType("registry")

    class _Registry(dict):
        def __getitem__(self, key: str) -> Any:  # type: ignore[override]
            if key not in self:
                super().__setitem__(key, _noop_alignment)
            return super().__getitem__(key)

    registry_module.COMMAND_REGISTRY = _Registry(
        {
            "alignment-metrics": alignment_module.alignment_metrics_cmd,
            "test-metrics": test_metrics_module.test_metrics_cmd,
        }
    )

    def _register(name: str, fn: Any) -> None:
        registry_module.COMMAND_REGISTRY[name] = fn

    registry_module.register = _register  # type: ignore[attr-defined]
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.registry",
        registry_module,
    )

    for module_name in [
        "devsynth.application.cli",
        "devsynth.application.cli.cli_commands",
        "devsynth.application.cli.commands.metrics_cmds",
        "devsynth.application.cli.commands.run_tests_cmd",
    ]:
        sys.modules.pop(module_name, None)

    return importlib.import_module("devsynth.application.cli.commands.run_tests_cmd")


def _build_minimal_app(monkeypatch: pytest.MonkeyPatch) -> Typer:
    """Construct a Typer app exposing only the run-tests command."""

    cli_module = _load_cli_module(monkeypatch)
    app = Typer()
    app.command(name="run-tests")(cli_module.run_tests_cmd)
    return app


def _install_pytest_stubs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    collect_stdout_sequence: list[str] | None = None,
) -> tuple[list[dict[str, str]], list[list[str]]]:
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
    app = _build_minimal_app(monkeypatch)
    with caplog.at_level(logging.INFO, logger="devsynth.testing.run_tests"):
        result = runner.invoke(
            app,
            [
                "--smoke",
                "--speed=fast",
                "--no-parallel",
                "--maxfail=1",
            ],
            prog_name="run-tests",
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
    app = _build_minimal_app(monkeypatch)
    with caplog.at_level(logging.INFO, logger="devsynth.testing.run_tests"):
        result = runner.invoke(
            app,
            [
                "--smoke",
                "--speed=fast",
                "--no-parallel",
                "--maxfail=1",
            ],
            prog_name="run-tests",
        )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".coverage").exists()
    assert (tmp_path / "test_reports" / "coverage.json").exists()
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert any(
        "-p pytest_bdd.plugin" in env.get("PYTEST_ADDOPTS", "") for env in popen_envs
    )
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
    app = _build_minimal_app(monkeypatch)
    with caplog.at_level(logging.INFO, logger="devsynth.testing.run_tests"):
        result = runner.invoke(
            app,
            [
                "--speed=fast",
                "--speed=medium",
                "--no-parallel",
                "--maxfail=1",
            ],
            prog_name="run-tests",
        )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".coverage").exists()
    assert (tmp_path / "test_reports" / "coverage.json").exists()
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert len(popen_envs) == 1
    env = popen_envs[0]
    assert env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    assert "-p pytest_cov" in env.get("PYTEST_ADDOPTS", "")
    assert "-p pytest_bdd.plugin" in env.get("PYTEST_ADDOPTS", "")
    assert combine_calls and all(calls for calls in combine_calls)
    assert not list(tmp_path.glob(".coverage.fragment-*"))
    assert "-p pytest_cov appended" in result.stdout


@pytest.mark.fast
def test_fast_medium_preserves_existing_cov_fail_under(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Custom fail-under thresholds survive coverage plugin injection."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--cov-fail-under=95")

    popen_envs, _ = _install_pytest_stubs(monkeypatch)

    runner = CliRunner()
    app = _build_minimal_app(monkeypatch)
    result = runner.invoke(
        app,
        [
            "--speed=fast",
            "--speed=medium",
            "--no-parallel",
            "--maxfail=1",
        ],
        prog_name="run-tests",
    )

    assert result.exit_code == 0, result.stdout
    assert popen_envs, "Pytest subprocess should capture PYTEST_ADDOPTS"
    env = popen_envs[0]
    addopts = env.get("PYTEST_ADDOPTS", "")
    assert "--cov-fail-under=95" in addopts
    assert "-p pytest_cov" in addopts


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
    app = _build_minimal_app(monkeypatch)
    with caplog.at_level(logging.INFO, logger="devsynth.testing.run_tests"):
        result = runner.invoke(
            app,
            [
                "--speed=fast",
                "--speed=medium",
                "--no-parallel",
                "--maxfail=1",
            ],
            prog_name="run-tests",
        )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".coverage").exists()
    assert (tmp_path / "test_reports" / "coverage.json").exists()
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert len(popen_envs) == 1
    env = popen_envs[0]
    assert env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    assert "-p pytest_cov" in env.get("PYTEST_ADDOPTS", "")
    assert "-p pytest_bdd.plugin" in env.get("PYTEST_ADDOPTS", "")
    assert combine_calls and all(calls for calls in combine_calls)
    assert "marker fallback" in caplog.text


@pytest.mark.fast
def test_fast_profile_generates_coverage_and_exits_successfully(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Default fast profile produces coverage artifacts and a zero exit code."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    popen_envs, combine_calls = _install_pytest_stubs(monkeypatch)

    runner = CliRunner()
    app = _build_minimal_app(monkeypatch)
    result = runner.invoke(
        app,
        [
            "--target",
            "unit-tests",
            "--speed",
            "fast",
            "--no-parallel",
            "--maxfail=1",
        ],
        prog_name="run-tests",
    )

    assert result.exit_code == 0, result.stdout
    assert "Coverage 100.00% meets the 90% threshold" in result.stdout
    assert (tmp_path / ".coverage").exists()
    assert (tmp_path / "test_reports" / "coverage.json").exists()
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert popen_envs and all(
        "-p pytest_cov" in env.get("PYTEST_ADDOPTS", "") for env in popen_envs
    )
    assert popen_envs and all(
        "pytest_bdd" in env.get("PYTEST_ADDOPTS", "") for env in popen_envs
    )
    assert combine_calls, "coverage fragments should be consolidated"


@pytest.mark.fast
def test_fast_profile_missing_coverage_artifacts_returns_exit_code_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing coverage artifacts in fast profile should exit with code 1."""

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    app = _build_minimal_app(monkeypatch)
    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        lambda *a, **k: (True, "simulated run"),
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.coverage_artifacts_status",
        lambda: (False, "Coverage JSON missing at test_reports/coverage.json"),
    )
    result = runner.invoke(
        app,
        [
            "--target",
            "unit-tests",
            "--speed",
            "fast",
        ],
        prog_name="run-tests",
    )

    assert result.exit_code == 1
    assert "Coverage artifacts missing or empty" in result.stdout
