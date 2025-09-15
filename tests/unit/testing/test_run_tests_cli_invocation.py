"""CLI-facing tests for ``devsynth.testing.run_tests``.

These tests exercise the command construction logic the Typer ``run-tests``
command relies on without importing :mod:`run_tests_cmd`, ensuring coverage for
``devsynth.testing.run_tests`` remains isolated.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture(autouse=True)
def _patch_artifact_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent tests from mutating coverage artifacts on disk."""

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
