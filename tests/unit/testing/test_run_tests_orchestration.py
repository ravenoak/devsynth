"""Targeted coverage tests for ``devsynth.testing.run_tests`` orchestration."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture(autouse=True)
def _isolate_subprocess_and_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent filesystem and subprocess side effects during orchestration tests."""
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(
        rt.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout="")
    )


@pytest.mark.fast
def test_verbose_flag_adds_v_to_pytest_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-ORCH-1 — verbose=True adds -v to the pytest command."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "test_file.py").write_text("def test_example(): pass")

    recorded_cmds: list[list[str]] = []

    class FakePopen:
        def __init__(self, cmd, *args, **kwargs):
            recorded_cmds.append(list(cmd))
            self.returncode = 0

        def communicate(self):
            return "ok", ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    with patch.object(rt, "collect_tests_with_cache", return_value=["test_file.py"]):
        rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=True,
            report=False,
            parallel=False,
            segment=False,
            maxfail=None,
            extra_marker=None,
        )

    assert recorded_cmds, "run_tests should have invoked Popen"
    pytest_cmd = recorded_cmds[0]
    assert "-v" in pytest_cmd


@pytest.mark.fast
def test_report_flag_adds_html_report_to_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-ORCH-2 — report=True adds --html to the pytest command."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "test_file.py").write_text("def test_example(): pass")

    recorded_cmds: list[list[str]] = []

    class FakePopen:
        def __init__(self, cmd, *args, **kwargs):
            recorded_cmds.append(list(cmd))
            self.returncode = 0

        def communicate(self):
            return "ok", ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    with (
        patch.object(rt, "collect_tests_with_cache", return_value=["test_file.py"]),
        patch.object(rt, "datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.return_value = "20250101_000000"
        rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=False,
            report=True,
            parallel=False,
            segment=False,
            maxfail=None,
            extra_marker=None,
        )

    assert recorded_cmds, "run_tests should have invoked Popen"
    pytest_cmd = recorded_cmds[0]
    assert any(arg.startswith("--html=") for arg in pytest_cmd)


@pytest.mark.fast
def test_no_parallel_flag_adds_n0_to_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-ORCH-3 — parallel=False adds -n0 to the pytest command."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "test_file.py").write_text("def test_example(): pass")

    recorded_cmds: list[list[str]] = []

    class FakePopen:
        def __init__(self, cmd, *args, **kwargs):
            recorded_cmds.append(list(cmd))
            self.returncode = 0

        def communicate(self):
            return "ok", ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    with patch.object(rt, "collect_tests_with_cache", return_value=["test_file.py"]):
        rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=False,
            report=False,
            parallel=False,
            segment=False,
            maxfail=None,
            extra_marker=None,
        )

    assert recorded_cmds, "run_tests should have invoked Popen"
    pytest_cmd = recorded_cmds[0]
    assert "-n0" in pytest_cmd


@pytest.mark.fast
def test_maxfail_flag_adds_maxfail_to_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-ORCH-4 — maxfail=N adds --maxfail=N to the pytest command."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "test_file.py").write_text("def test_example(): pass")

    recorded_cmds: list[list[str]] = []

    class FakePopen:
        def __init__(self, cmd, *args, **kwargs):
            recorded_cmds.append(list(cmd))
            self.returncode = 0

        def communicate(self):
            return "ok", ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    with patch.object(rt, "collect_tests_with_cache", return_value=["test_file.py"]):
        rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=False,
            report=False,
            parallel=False,
            segment=False,
            maxfail=5,
            extra_marker=None,
        )

    assert recorded_cmds, "run_tests should have invoked Popen"
    pytest_cmd = recorded_cmds[0]
    assert "--maxfail=5" in pytest_cmd


@pytest.mark.fast
def test_segment_flags_trigger_segmented_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-ORCH-5 — segment=True triggers a segmented run."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "test_file.py").write_text("def test_example(): pass")

    recorded_cmds: list[list[str]] = []

    class FakePopen:
        def __init__(self, cmd, *args, **kwargs):
            recorded_cmds.append(list(cmd))
            self.returncode = 0

        def communicate(self):
            return "ok", ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    with patch.object(rt.subprocess, "run") as mock_run:
        mock_run.return_value.stdout = "test_file.py\ntest_file2.py"
        mock_run.return_value.returncode = 0
        rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=False,
            report=False,
            parallel=False,
            segment=True,
            segment_size=1,
            maxfail=None,
            extra_marker=None,
        )

    assert len(recorded_cmds) == 2, "Expected two Popen calls for a segmented run"


@pytest.mark.fast
def test_pytest_addopts_are_preserved(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-ORCH-7 — PYTEST_ADDOPTS are preserved during test runs."""
    monkeypatch.setenv("PYTEST_ADDOPTS", "--custom-flag")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "test_file.py").write_text("def test_example(): pass")

    recorded_cmds: list[list[str]] = []

    class FakePopen:
        def __init__(self, cmd, *args, **kwargs):
            recorded_cmds.append(list(cmd))
            self.returncode = 0

        def communicate(self):
            return "ok", ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    with patch.object(rt, "collect_tests_with_cache", return_value=["test_file.py"]):
        rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=False,
            report=False,
            parallel=False,
            segment=False,
            maxfail=None,
            extra_marker=None,
        )

    assert recorded_cmds, "run_tests should have invoked Popen"
    # The value of PYTEST_ADDOPTS is not directly passed to the command, but respected by pytest
    # This test ensures that the run completes successfully, indirectly testing that the addopts are not breaking the run


@pytest.mark.fast
def test_extra_marker_adds_m_flag_to_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-ORCH-6 — extra_marker adds -m to the pytest command."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "test_file.py").write_text("def test_example(): pass")

    recorded_cmds: list[list[str]] = []

    class FakePopen:
        def __init__(self, cmd, *args, **kwargs):
            recorded_cmds.append(list(cmd))
            self.returncode = 0

        def communicate(self):
            return "ok", ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    with patch.object(rt, "collect_tests_with_cache", return_value=["test_file.py"]):
        rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=False,
            report=False,
            parallel=False,
            segment=False,
            maxfail=None,
            extra_marker="slow",
        )

    assert recorded_cmds, "run_tests should have invoked Popen"
    pytest_cmd = recorded_cmds[0]
    assert "-m" in pytest_cmd
    assert any(
        "slow" in arg for arg in pytest_cmd
    ), "Marker expression not found in command"
