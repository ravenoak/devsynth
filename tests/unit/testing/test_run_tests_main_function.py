"""Targeted coverage tests for the main run_tests function."""

from __future__ import annotations

import os
import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_run_tests_single_execution_success(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-1 — run_tests executes single batch successfully."""
    fake_env = {"TEST": "value"}

    def fake_popen(cmd, **kwargs):
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Test output", "")
        mock_process.returncode = 0
        return mock_process

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=True,
        report=True,
        parallel=False,
        env=fake_env,
    )

    assert success is True
    assert "Test output" in output


@pytest.mark.fast
def test_run_tests_single_execution_failure(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-2 — run_tests handles test failures."""

    def fake_popen(cmd, **kwargs):
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Test failed", "")
        mock_process.returncode = 1
        return mock_process

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "_failure_tips", lambda code, cmd: "\nFailure tips")

    success, output = rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False
    )

    assert success is False
    assert "Test failed" in output
    assert "Failure tips" in output


@pytest.mark.fast
def test_run_tests_segmented_execution(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-3 — run_tests handles segmented execution."""

    def fake_collect_tests(target, speed):
        return ["test1.py::test_a", "test2.py::test_b", "test3.py::test_c"]

    def fake_popen(cmd, **kwargs):
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Segment output", "")
        mock_process.returncode = 0
        return mock_process

    monkeypatch.setattr(rt, "collect_tests_with_cache", fake_collect_tests)
    monkeypatch.setattr(rt, "_sanitize_node_ids", lambda ids: ids)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        segment_size=2,
        parallel=False,
    )

    assert success is True
    assert "Segment output" in output


@pytest.mark.fast
def test_run_tests_marker_expression_building(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-4 — run_tests builds correct marker expressions."""
    captured_cmd = None

    def fake_run_single_test_batch(node_ids, marker_expr, **kwargs):
        nonlocal captured_cmd
        # Simulate the command that would be built
        captured_cmd = ["python", "-m", "pytest"] + node_ids + ["-m", marker_expr]
        return True, "Tests passed"

    # Mock the test collection to return some dummy node IDs
    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed: ["tests/unit/test_example.py"],
    )
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single_test_batch)

    rt.run_tests(
        target="unit-tests",
        speed_categories=["fast", "medium"],
        extra_marker="requires_resource('test')",
        parallel=False,
    )

    # Check that marker expression was built correctly
    marker_idx = captured_cmd.index("-m")
    marker_expr = captured_cmd[marker_idx + 1]
    assert "not memory_intensive" in marker_expr
    assert "(fast or medium)" in marker_expr
    assert "(requires_resource('test'))" in marker_expr


@pytest.mark.fast
def test_run_tests_env_defaults(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-5 — run_tests uses os.environ when env is None."""
    captured_env = None

    def fake_popen(cmd, **kwargs):
        nonlocal captured_env
        captured_env = kwargs.get("env")
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        return mock_process

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    # Set a test env var
    original_env = os.environ.copy()
    os.environ["TEST_VAR"] = "test_value"

    try:
        rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            parallel=False,
            env=None,  # Should default to os.environ
        )

        assert captured_env is not None
        assert captured_env["TEST_VAR"] == "test_value"
    finally:
        os.environ.clear()
        os.environ.update(original_env)


@pytest.mark.fast
def test_run_tests_exception_handling(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-6 — run_tests handles subprocess exceptions."""

    def fake_popen(*args, **kwargs):
        raise OSError("Subprocess failed")

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    success, output = rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False
    )

    assert success is False
    assert "Failed to run tests: Subprocess failed" in output


@pytest.mark.fast
def test_run_tests_exit_code_5_success(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-7 — run_tests treats exit code 5 (no tests) as success."""

    def fake_popen(cmd, **kwargs):
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("No tests collected", "")
        mock_process.returncode = 5  # No tests collected
        return mock_process

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    success, output = rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False
    )

    assert success is True
    assert "No tests collected" in output


@pytest.mark.fast
def test_run_tests_keyword_filter(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-8 — run_tests applies keyword filter."""
    captured_cmd = None

    def fake_popen(cmd, **kwargs):
        nonlocal captured_cmd
        captured_cmd = cmd
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        return mock_process

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        keyword_filter="test_specific",
        parallel=False,
    )

    # Check that keyword filter was applied
    k_idx = captured_cmd.index("-k")
    keyword = captured_cmd[k_idx + 1]
    assert keyword == "test_specific"


@pytest.mark.fast
def test_run_tests_maxfail_option(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-9 — run_tests applies maxfail option."""
    captured_cmd = None

    def fake_popen(cmd, **kwargs):
        nonlocal captured_cmd
        captured_cmd = cmd
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        return mock_process

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    rt.run_tests(
        target="unit-tests", speed_categories=["fast"], maxfail=3, parallel=False
    )

    # Check that maxfail was applied
    maxfail_idx = captured_cmd.index("--maxfail")
    maxfail_value = captured_cmd[maxfail_idx + 1]
    assert maxfail_value == "3"


@pytest.mark.fast
def test_run_tests_smoke_mode_plugin_injection(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-10 — run_tests injects plugins in smoke mode."""
    captured_env = None

    def fake_popen(cmd, **kwargs):
        nonlocal captured_env
        captured_env = kwargs.get("env", {}).copy()
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        return mock_process

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    test_env = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}

    rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False, env=test_env
    )

    # Check that plugins were injected
    assert "PYTEST_ADDOPTS" in captured_env
    addopts = captured_env["PYTEST_ADDOPTS"]
    assert "-p pytest_cov" in addopts
    assert "-p pytest_bdd" in addopts
