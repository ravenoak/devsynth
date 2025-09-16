"""CLI-facing tests for ``devsynth.testing.run_tests``.

These tests exercise the command construction logic the Typer ``run-tests``
command relies on without importing :mod:`run_tests_cmd`, ensuring coverage for
``devsynth.testing.run_tests`` remains isolated.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import types
import sys
import json
import logging

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture(autouse=True)
def _patch_artifact_helpers(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Prevent tests from mutating coverage artifacts on disk."""

    if request.node.get_closest_marker("allow_real_coverage_artifacts"):
        return

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)


@pytest.mark.fast
def test_cli_marker_expression_includes_extra_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: RUN-TESTS-CLI-ARGS-1 — CLI marker flag augments default filters."""

    commands: list[list[str]] = []

    class DummyProcess:
        def __init__(
            self,
            cmd: list[str],
            stdout=None,
            stderr=None,
            text: bool = False,
            env: dict[str, str] | None = None,
        ) -> None:
            commands.append(cmd)
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("collected 1 item", "")

    monkeypatch.setattr(rt.subprocess, "Popen", DummyProcess)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        extra_marker="custom_marker",
    )

    assert success is True
    assert "collected 1 item" in output
    assert commands, "Expected to capture a pytest invocation"

    cmd = commands[0]
    assert f"--cov={rt.COVERAGE_TARGET}" in cmd
    assert f"--cov-report=json:{rt.COVERAGE_JSON_PATH}" in cmd
    assert f"--cov-report=html:{rt.COVERAGE_HTML_DIR}" in cmd

    assert cmd[-2] == "-m"
    assert cmd[-1] == "(not memory_intensive) and (custom_marker)"


@pytest.mark.fast
def test_cli_failure_surfaces_actionable_tips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: RUN-TESTS-CLI-ERROR-1 — CLI surfaces troubleshooting tips."""

    commands: list[list[str]] = []

    class FailingProcess:
        def __init__(
            self,
            cmd: list[str],
            stdout=None,
            stderr=None,
            text: bool = False,
            env: dict[str, str] | None = None,
        ) -> None:
            commands.append(cmd)
            raise RuntimeError("simulated failure")

    monkeypatch.setattr(rt.subprocess, "Popen", FailingProcess)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
    )

    assert success is False
    assert "simulated failure" in output
    assert commands, "Expected to capture the failing pytest command"

    expected_tips = rt._failure_tips(-1, commands[0])
    assert expected_tips in output


@pytest.mark.fast
def test_cli_segment_batches_follow_segment_size(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """ReqID: RUN-TESTS-CLI-SEGMENT-1 — Segmentation obeys CLI batch sizing."""

    # Point the unit-tests target to a temporary directory with synthetic tests
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))

    file_a = tmp_path / "test_alpha.py"
    file_b = tmp_path / "test_beta.py"
    file_a.write_text("def test_one():\n    assert True\n")
    file_b.write_text("def test_two():\n    assert True\n")

    node_ids = [
        f"{file_a}::test_one",
        f"{file_a}::test_two",
        f"{file_b}::test_three",
    ]

    def fake_collect(
        cmd: list[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
    ) -> SimpleNamespace:
        assert "--collect-only" in cmd
        return SimpleNamespace(stdout="\n".join(node_ids), stderr="", returncode=0)

    commands: list[list[str]] = []

    class BatchProcess:
        def __init__(
            self,
            cmd: list[str],
            stdout=None,
            stderr=None,
            text: bool = False,
            env: dict[str, str] | None = None,
        ) -> None:
            commands.append(cmd)
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("ok", "")

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", BatchProcess)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=2,
    )

    assert success is True
    assert "ok" in output
    assert len(commands) == 2, "Expected two batches for three node ids with size 2"

    first_batch = [part for part in commands[0] if part in node_ids]
    second_batch = [part for part in commands[1] if part in node_ids]
    assert first_batch == node_ids[:2]
    assert second_batch == node_ids[2:]


@pytest.mark.fast
def test_cli_keyword_filter_handles_resource_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """ReqID: RUN-TESTS-CLI-ARGS-2 — resource markers trigger keyword filtering."""

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))

    test_file = tmp_path / "test_lmstudio.py"
    test_file.write_text("def test_stub():\n    assert True\n")

    collect_commands: list[list[str]] = []

    def fake_collect(
        cmd: list[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
    ) -> SimpleNamespace:
        collect_commands.append(cmd)
        return SimpleNamespace(stdout=f"{test_file.name}::test_stub\n", stderr="", returncode=0)

    run_commands: list[list[str]] = []

    class DummyProcess:
        def __init__(
            self,
            cmd: list[str],
            stdout=None,
            stderr=None,
            text: bool = False,
            env: dict[str, str] | None = None,
        ) -> None:
            run_commands.append(cmd)
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("ok", "")

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", DummyProcess)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        extra_marker="requires_resource('lmstudio')",
    )

    assert success is True
    assert "ok" in output
    assert collect_commands, "Expected collection command to run"
    assert run_commands, "Expected run command to execute"

    collect_tail = collect_commands[0][-2:]
    assert collect_tail == ["-k", "lmstudio"], collect_commands[0]
    assert test_file.name + "::test_stub" in run_commands[0]


@pytest.mark.fast
def test_cli_report_mode_adds_html_argument(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """ReqID: RUN-TESTS-CLI-REPORT-1 — report flag appends HTML output options."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))

    test_file = tmp_path / "test_report.py"
    test_file.write_text("def test_report():\n    assert True\n")

    def fake_collect(
        cmd: list[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
    ) -> SimpleNamespace:
        return SimpleNamespace(stdout=f"{test_file.name}::test_report\n", stderr="", returncode=0)

    run_commands: list[list[str]] = []

    class DummyProcess:
        def __init__(
            self,
            cmd: list[str],
            stdout=None,
            stderr=None,
            text: bool = False,
            env: dict[str, str] | None = None,
        ) -> None:
            run_commands.append(cmd)
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("report ok", "")

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", DummyProcess)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=True,
        parallel=False,
    )

    assert success is True
    assert "report ok" in output
    assert run_commands, "Expected report-mode command to run"

    html_args = [arg for arg in run_commands[0] if arg.startswith("--html=")]
    assert html_args, run_commands[0]
    assert html_args[0].startswith("--html=test_reports/")
    assert (tmp_path / "test_reports").exists()


@pytest.mark.fast
@pytest.mark.allow_real_coverage_artifacts
def test_run_tests_generates_coverage_totals(
    monkeypatch: pytest.MonkeyPatch, tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """ReqID: RUN-TESTS-COVERAGE-1 — Successful run yields coverage totals."""

    monkeypatch.chdir(tmp_path)

    stub_module = types.ModuleType("coverage")

    class StubCoverage:
        json_outputs: list[str] = []
        html_outputs: list[str] = []

        def __init__(self, data_file: str = ".coverage") -> None:
            self.data_file = data_file

        def load(self) -> None:  # pragma: no cover - simple stub
            return None

        def get_data(self) -> SimpleNamespace:
            return SimpleNamespace(measured_files=lambda: ["stub.py"])

        def html_report(self, directory: str) -> None:
            StubCoverage.html_outputs.append(directory)
            out_dir = Path(directory)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text("<html><body>ok</body></html>")

        def json_report(self, outfile: str) -> None:
            StubCoverage.json_outputs.append(outfile)
            Path(outfile).write_text(
                json.dumps({"totals": {"percent_covered": 99.0}})
            )

    stub_module.Coverage = StubCoverage  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "coverage", stub_module)
    (tmp_path / ".coverage").write_text("stub")

    caplog.set_level(logging.WARNING, logger="devsynth.testing.run_tests")
    rt._ensure_coverage_artifacts()

    assert StubCoverage.json_outputs, "Expected coverage JSON to be generated"

    coverage_json = tmp_path / rt.COVERAGE_JSON_PATH
    assert coverage_json.exists()
    payload = json.loads(coverage_json.read_text())
    totals = payload.get("totals") if isinstance(payload, dict) else None
    assert isinstance(totals, dict)
    assert "percent_covered" in totals

    html_index = tmp_path / rt.COVERAGE_HTML_DIR / "index.html"
    assert html_index.exists()
    assert "No coverage data available" not in html_index.read_text()


@pytest.mark.fast
@pytest.mark.allow_real_coverage_artifacts
def test_run_tests_skips_placeholder_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """ReqID: RUN-TESTS-COVERAGE-2 — Missing coverage data avoids placeholders."""

    monkeypatch.chdir(tmp_path)
    caplog.set_level(logging.WARNING, logger="devsynth.testing.run_tests")
    rt._ensure_coverage_artifacts()
    coverage_json = tmp_path / rt.COVERAGE_JSON_PATH
    html_dir = tmp_path / rt.COVERAGE_HTML_DIR

    assert not coverage_json.exists()
    assert not html_dir.exists()

    warning_messages = [record.getMessage() for record in caplog.records]
    assert any("Coverage artifact generation skipped" in msg for msg in warning_messages)
