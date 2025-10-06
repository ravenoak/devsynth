"""Targeted coverage tests for the main run_tests function."""

from __future__ import annotations

import os

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_run_tests_single_execution_success(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-1 — run_tests executes single batch successfully."""
    fake_env = {"TEST": "value"}

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: ["tests/unit/test_example.py::test_case"],
    )

    def fake_run_single(node_ids, marker_expr, **kwargs):
        return True, "Test output\n", {"command": ["pytest"], "returncode": 0}

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def inject_cov(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_cov".strip()
        return True

    def inject_bdd(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_bdd".strip()
        return True

    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", inject_cov)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", inject_bdd)

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

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: ["tests/unit/test_example.py::test_case"],
    )

    def fake_run_single(node_ids, marker_expr, **kwargs):
        return False, "Test failed\nFailure tips\n", {
            "command": ["pytest"],
            "returncode": 1,
        }

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def inject_cov(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_cov".strip()
        return True

    def inject_bdd(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_bdd".strip()
        return True

    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", inject_cov)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", inject_bdd)

    success, output = rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False
    )

    assert success is False
    assert "Test failed" in output
    assert "Failure tips" in output


@pytest.mark.fast
def test_run_tests_segmented_execution(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-3 — run_tests handles segmented execution."""

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: [
            "test1.py::test_a",
            "test2.py::test_b",
            "test3.py::test_c",
        ],
    )
    monkeypatch.setattr(rt, "_sanitize_node_ids", lambda ids: ids)

    segment_calls: list[list[str]] = []

    def fake_run_single(node_ids, marker_expr, **kwargs):
        segment_calls.append(list(node_ids))
        return True, "Segment output\n", {
            "command": ["pytest"],
            "returncode": 0,
            "started_at": "start",
            "completed_at": "end",
        }

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def inject_cov(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_cov".strip()
        return True

    def inject_bdd(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_bdd".strip()
        return True

    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", inject_cov)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", inject_bdd)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        segment_size=2,
        parallel=False,
    )

    assert success is True
    assert "Segment output" in output
    assert segment_calls == [["test1.py::test_a", "test2.py::test_b"], ["test3.py::test_c"]]


@pytest.mark.fast
def test_run_tests_marker_expression_building(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-4 — run_tests builds correct marker expressions."""
    captured_cmd = None

    captured_kwargs: dict[str, object] = {}

    def fake_run_single_test_batch(node_ids, marker_expr, **kwargs):
        nonlocal captured_cmd
        # Simulate the command that would be built
        captured_cmd = ["python", "-m", "pytest"] + node_ids + ["-m", marker_expr]
        captured_kwargs.update(kwargs)
        return True, "Tests passed\n", {
            "command": captured_cmd,
            "returncode": 0,
            "started_at": "start",
            "completed_at": "end",
        }

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
    marker_indices = [i for i, token in enumerate(captured_cmd) if token == "-m"]
    marker_expr = captured_cmd[marker_indices[-1] + 1]
    assert "not memory_intensive" in marker_expr
    assert "(fast or medium)" in marker_expr
    assert "requires_resource" not in marker_expr
    assert captured_kwargs.get("keyword_filter") == "test"


@pytest.mark.fast
def test_run_tests_env_defaults(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-5 — run_tests uses os.environ when env is None."""
    captured_env = None

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: ["tests/unit/test_example.py::test_case"],
    )

    def fake_run_single(node_ids, marker_expr, **kwargs):
        nonlocal captured_env
        captured_env = kwargs.get("env")
        return True, "", {
            "command": ["pytest"],
            "returncode": 0,
            "started_at": "start",
            "completed_at": "end",
        }

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def inject_cov(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_cov".strip()
        return True

    def inject_bdd(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_bdd".strip()
        return True

    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", inject_cov)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", inject_bdd)

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

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: ["tests/unit/test_example.py::test_case"],
    )

    def boom(*_args, **_kwargs):
        raise OSError("Subprocess failed")

    monkeypatch.setattr(rt.subprocess, "Popen", boom)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
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

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: ["tests/unit/test_example.py::test_case"],
    )

    def fake_run_single(node_ids, marker_expr, **kwargs):
        return True, "No tests collected\n", {
            "command": ["pytest"],
            "returncode": 5,
            "started_at": "start",
            "completed_at": "end",
        }

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    success, output = rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False
    )

    assert success is True
    assert "No tests collected" in output


@pytest.mark.fast
def test_run_tests_dry_run_skips_execution(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-8 — dry-run previews command without running pytest."""

    monkeypatch.setattr(
        rt, "collect_tests_with_cache", lambda *_args, **_kwargs: [
            "tests/unit/test_example.py::test_case"
        ]
    )

    def fail_reset() -> None:  # pragma: no cover - should not run
        raise AssertionError("_reset_coverage_artifacts should not run in dry mode")

    def fail_ensure() -> None:  # pragma: no cover - should not run
        raise AssertionError("_ensure_coverage_artifacts should not run in dry mode")

    def boom(*_args, **_kwargs):  # pragma: no cover - subprocess must not spawn
        raise AssertionError("Subprocess should not spawn during dry run")

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", fail_reset)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", fail_ensure)
    monkeypatch.setattr(rt.subprocess, "Popen", boom)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: False)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        parallel=False,
        dry_run=True,
    )

    assert success is True
    assert "Dry run" in output


@pytest.mark.fast
def test_run_tests_keyword_filter(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-8 — run_tests applies keyword filter."""
    captured_cmd = None

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: ["tests/unit/test_example.py::test_case"],
    )

    captured_kwargs: dict[str, object] = {}

    def fake_run_single(node_ids, marker_expr, **kwargs):
        captured_kwargs.update(kwargs)
        return True, "", {
            "command": ["pytest"],
            "returncode": 0,
            "started_at": "start",
            "completed_at": "end",
        }

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        keyword_filter="test_specific",
        parallel=False,
    )

    assert captured_kwargs.get("keyword_filter") == "test_specific"


@pytest.mark.fast
def test_run_tests_maxfail_option(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-9 — run_tests applies maxfail option."""
    captured_cmd = None

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: ["tests/unit/test_example.py::test_case"],
    )

    captured_kwargs: dict[str, object] = {}

    def fake_run_single(node_ids, marker_expr, **kwargs):
        captured_kwargs.update(kwargs)
        return True, "", {
            "command": ["pytest"],
            "returncode": 0,
            "started_at": "start",
            "completed_at": "end",
        }

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: True)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: True)

    rt.run_tests(
        target="unit-tests", speed_categories=["fast"], maxfail=3, parallel=False
    )

    assert captured_kwargs.get("maxfail") == 3


@pytest.mark.fast
def test_run_tests_smoke_mode_plugin_injection(monkeypatch):
    """ReqID: RUN-TESTS-MAIN-10 — run_tests injects plugins in smoke mode."""
    captured_env = None

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: ["tests/unit/test_example.py::test_case"],
    )

    def fake_run_single(node_ids, marker_expr, **kwargs):
        nonlocal captured_env
        captured_env = kwargs.get("env", {})
        return True, "", {
            "command": ["pytest"],
            "returncode": 0,
            "started_at": "start",
            "completed_at": "end",
        }

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def inject_cov(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_cov".strip()
        return True

    def inject_bdd(env: dict[str, str]) -> bool:
        existing = env.get("PYTEST_ADDOPTS", "").strip()
        env["PYTEST_ADDOPTS"] = f"{existing} -p pytest_bdd".strip()
        return True

    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", inject_cov)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", inject_bdd)

    test_env = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}

    rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False, env=test_env
    )

    # Check that plugins were injected
    assert "PYTEST_ADDOPTS" in captured_env
    addopts = captured_env["PYTEST_ADDOPTS"]
    assert "-p pytest_cov" in addopts
    assert "-p pytest_bdd" in addopts
