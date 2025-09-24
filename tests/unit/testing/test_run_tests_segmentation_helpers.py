"""Targeted coverage tests for segmentation helper functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_run_segmented_tests_single_speed(monkeypatch):
    """ReqID: RUN-TESTS-SEG-1 — _run_segmented_tests handles single speed category."""

    def fake_collect_tests(target, speed):
        return [
            "test1.py::test_a",
            "test2.py::test_b",
            "test3.py::test_c",
            "test4.py::test_d",
        ]

    def fake_sanitize(ids):
        return ids

    def fake_single_batch(test_path, **kwargs):
        return True, f"Batch output for: {test_path[:20]}..."

    monkeypatch.setattr(rt, "collect_tests_with_cache", fake_collect_tests)
    monkeypatch.setattr(rt, "_sanitize_node_ids", fake_sanitize)
    monkeypatch.setattr(rt, "_run_single_test_batch", fake_single_batch)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    success, output = rt._run_segmented_tests(
        target="unit-tests",
        speed_categories=["fast"],
        marker_expr="fast and not memory_intensive",
        test_path="tests/unit/",
        verbose=False,
        report=True,
        parallel=False,
        segment_size=2,
        maxfail=None,
        keyword_filter=None,
        env={},
    )

    assert success is True
    assert "Batch output for:" in output


@pytest.mark.fast
def test_run_segmented_tests_multiple_speeds(monkeypatch):
    """ReqID: RUN-TESTS-SEG-2 — _run_segmented_tests handles multiple speed categories."""

    def fake_collect_tests(target, speed):
        if speed == "fast":
            return ["test1.py::test_fast"]
        elif speed == "medium":
            return ["test2.py::test_medium"]
        return []

    def fake_sanitize(ids):
        return ids

    def fake_single_batch(test_path, **kwargs):
        return True, f"Batch for {test_path}"

    monkeypatch.setattr(rt, "collect_tests_with_cache", fake_collect_tests)
    monkeypatch.setattr(rt, "_sanitize_node_ids", fake_sanitize)
    monkeypatch.setattr(rt, "_run_single_test_batch", fake_single_batch)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    success, output = rt._run_segmented_tests(
        target="unit-tests",
        speed_categories=["fast", "medium"],
        marker_expr="(fast or medium) and not memory_intensive",
        test_path="tests/unit/",
        verbose=False,
        report=False,
        parallel=False,
        segment_size=1,
        maxfail=None,
        keyword_filter=None,
        env={},
    )

    assert success is True
    assert "test1.py::test_fast" in output
    assert "test2.py::test_medium" in output


@pytest.mark.fast
def test_run_segmented_tests_no_tests_found(monkeypatch):
    """ReqID: RUN-TESTS-SEG-3 — _run_segmented_tests handles no tests found."""

    def fake_collect_tests(target, speed):
        return []

    monkeypatch.setattr(rt, "collect_tests_with_cache", fake_collect_tests)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    success, output = rt._run_segmented_tests(
        target="unit-tests",
        speed_categories=["fast"],
        marker_expr="fast and not memory_intensive",
        test_path="tests/unit/",
        verbose=False,
        report=False,
        parallel=False,
        segment_size=2,
        maxfail=None,
        keyword_filter=None,
        env={},
    )

    assert success is True
    assert output == ""


@pytest.mark.fast
def test_run_segmented_tests_failure_with_maxfail(monkeypatch):
    """ReqID: RUN-TESTS-SEG-4 — _run_segmented_tests stops on failure with maxfail."""

    def fake_collect_tests(target, speed):
        return [
            "test1.py::test_a",
            "test2.py::test_b",
            "test3.py::test_c",
            "test4.py::test_d",
        ]

    def fake_sanitize(ids):
        return ids

    call_count = 0

    def fake_single_batch(test_path, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return False, "First segment failed"
        return True, "Should not be called"

    monkeypatch.setattr(rt, "collect_tests_with_cache", fake_collect_tests)
    monkeypatch.setattr(rt, "_sanitize_node_ids", fake_sanitize)
    monkeypatch.setattr(rt, "_run_single_test_batch", fake_single_batch)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    success, output = rt._run_segmented_tests(
        target="unit-tests",
        speed_categories=["fast"],
        marker_expr="fast and not memory_intensive",
        test_path="tests/unit/",
        verbose=False,
        report=False,
        parallel=False,
        segment_size=2,
        maxfail=1,
        keyword_filter=None,
        env={},
    )

    assert success is False
    assert "First segment failed" in output
    assert call_count == 1  # Should stop after first failure


@pytest.mark.fast
def test_run_single_test_batch_command_building(monkeypatch):
    """ReqID: RUN-TESTS-BATCH-1 — _run_single_test_batch builds correct command."""
    captured_cmd = None

    def fake_popen(cmd, **kwargs):
        nonlocal captured_cmd
        captured_cmd = cmd
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        return mock_process

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, output = rt._run_single_test_batch(
        test_path="tests/unit/",
        marker_expr="fast and not memory_intensive",
        verbose=True,
        report=True,
        parallel=True,
        maxfail=5,
        keyword_filter="test_something",
        env={},
    )

    assert success is True
    assert captured_cmd[0:3] == [rt.sys.executable, "-m", "pytest"]
    assert "tests/unit/" in captured_cmd
    assert "-m" in captured_cmd
    assert "fast and not memory_intensive" in captured_cmd
    assert f"--cov={rt.COVERAGE_TARGET}" in captured_cmd
    assert "-v" in captured_cmd
    assert "-n" in captured_cmd
    assert "auto" in captured_cmd
    assert "--maxfail" in captured_cmd
    assert "5" in captured_cmd
    assert "-k" in captured_cmd
    assert "test_something" in captured_cmd


@pytest.mark.fast
def test_run_single_test_batch_multiple_node_ids():
    """ReqID: RUN-TESTS-BATCH-2 — _run_single_test_batch handles multiple node IDs."""
    captured_cmd = None

    def fake_popen(cmd, **kwargs):
        nonlocal captured_cmd
        captured_cmd = cmd
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        return mock_process

    with patch.object(rt.subprocess, "Popen", fake_popen):
        success, output = rt._run_single_test_batch(
            test_path="test1.py::test_a test2.py::test_b",
            marker_expr="fast",
            verbose=False,
            report=False,
            parallel=False,
            maxfail=None,
            keyword_filter=None,
            env={},
        )

    assert success is True
    assert "test1.py::test_a" in captured_cmd
    assert "test2.py::test_b" in captured_cmd


@pytest.mark.fast
def test_run_single_test_batch_smoke_mode_env():
    """ReqID: RUN-TESTS-BATCH-3 — _run_single_test_batch handles smoke mode env."""
    captured_env = None

    def fake_popen(cmd, **kwargs):
        nonlocal captured_env
        captured_env = kwargs.get("env", {}).copy()
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        return mock_process

    test_env = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "--tb=short"}

    with patch.object(rt.subprocess, "Popen", fake_popen):
        success, output = rt._run_single_test_batch(
            test_path="tests/unit/",
            marker_expr="fast",
            verbose=False,
            report=False,
            parallel=False,
            maxfail=None,
            keyword_filter=None,
            env=test_env,
        )

    assert success is True
    assert "PYTEST_ADDOPTS" in captured_env
    addopts = captured_env["PYTEST_ADDOPTS"]
    assert "--tb=short" in addopts
    assert "-p pytest_cov" in addopts
    assert "-p pytest_bdd" in addopts


@pytest.mark.fast
def test_run_single_test_batch_no_parallel():
    """ReqID: RUN-TESTS-BATCH-4 — _run_single_test_batch respects no-parallel."""
    captured_cmd = None

    def fake_popen(cmd, **kwargs):
        nonlocal captured_cmd
        captured_cmd = cmd
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        return mock_process

    with patch.object(rt.subprocess, "Popen", fake_popen):
        success, output = rt._run_single_test_batch(
            test_path="tests/unit/",
            marker_expr="fast",
            verbose=False,
            report=False,
            parallel=False,  # Explicitly disabled
            maxfail=None,
            keyword_filter=None,
            env={},
        )

    assert success is True
    # Should not contain -n auto when parallel is False
    assert "-n" not in captured_cmd or "auto" not in captured_cmd
