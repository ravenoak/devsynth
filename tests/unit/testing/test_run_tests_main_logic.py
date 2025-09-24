from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture(autouse=True)
def _isolate_artifact_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent filesystem side effects during helper orchestration tests."""

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)


@pytest.fixture
def mock_subprocess_run(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    recorded_calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
        recorded_calls.append(cmd)
        if "--collect-only" in cmd:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    return recorded_calls


@pytest.fixture
def mock_subprocess_popen(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[list[str], dict[str, str]]]:
    recorded_calls: list[tuple[list[str], dict[str, str]]] = []

    class FakePopen:
        def __init__(
            self, cmd: list[str], env: dict[str, str] | None = None, **kwargs: Any
        ) -> None:
            # Capture the actual environment that Popen would use
            final_env = os.environ.copy()
            if env:
                final_env.update(env)
            recorded_calls.append((cmd, final_env))
            self.returncode = 0
            self._stdout = ""
            self._stderr = ""

        def communicate(self) -> tuple[str, str]:
            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)
    return recorded_calls


@pytest.mark.fast
def test_collect_tests_with_cache_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", tmp_path)
    cache_file = (
        tmp_path / "unit-tests_all_tests.json"
    )  # This is the expected cache file name

    collect_output = """
    test_module.py::test_func_a
    test_module.py::test_func_b
    """.strip()

    def fake_run(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
        assert "--collect-only" in cmd
        return SimpleNamespace(returncode=0, stdout=collect_output, stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    tests = rt.collect_tests_with_cache(target="unit-tests", speed_category=None)  # type: ignore[attr-defined]
    assert tests == ["test_module.py::test_func_a", "test_module.py::test_func_b"]
    assert cache_file.exists()
    cached_data = json.loads(cache_file.read_text())
    assert cached_data["tests"] == [
        "test_module.py::test_func_a",
        "test_module.py::test_func_b",
    ]


@pytest.mark.fast
def test_collect_tests_with_cache_from_existing_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", tmp_path)
    cache_file = (
        tmp_path / "unit-tests_all_tests.json"
    )  # This is the expected cache file name

    cached_tests = [
        "cached_module.py::cached_func_a",
        "cached_module.py::cached_func_b",
    ]
    cached_data = {
        "timestamp": datetime.now().isoformat(),
        "tests": cached_tests,
        "fingerprint": {
            "latest_mtime": 12345.0,  # Dummy mtime
            "category_expr": "not memory_intensive",  # Default category_expr
            "test_path": str(tmp_path),  # Mocked test_path
        },
    }
    cache_file.write_text(json.dumps(cached_data))

    # Ensure subprocess.run is NOT called
    def fake_run_should_not_be_called(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
        raise AssertionError("subprocess.run should not be called when using cache")

    monkeypatch.setattr(rt.subprocess, "run", fake_run_should_not_be_called)
    monkeypatch.setattr(
        rt, "_latest_mtime", lambda root: 12345.0
    )  # Mock _latest_mtime to match cached value
    monkeypatch.setattr(
        rt, "_latest_mtime", lambda root: 12345.0
    )  # Mock _latest_mtime to match cached value

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    tests = rt.collect_tests_with_cache(target="unit-tests", speed_category=None)
    assert tests == [
        "cached_module.py::cached_func_a",
        "cached_module.py::cached_func_b",
    ]
    assert cache_file.exists()


@pytest.mark.fast
def test_collect_tests_with_cache_collection_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test test collection failure scenario."""
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", tmp_path)
    cache_file = (
        tmp_path / "unit-tests_all_tests.json"
    )  # This is the expected cache file name

    def fake_run_fail(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(returncode=1, stdout="", stderr="Collection failed")

    monkeypatch.setattr(rt.subprocess, "run", fake_run_fail)

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    with pytest.raises(RuntimeError, match="Test collection failed"):
        rt.collect_tests_with_cache(target="unit-tests", speed_category=None)
    assert not cache_file.exists()


@pytest.mark.fast
def test_run_tests_basic_execution(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test basic run_tests execution with default parameters."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_pass(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    success, output = rt.run_tests(target="unit-tests")

    assert success is True
    assert output == ""  # Default mock_subprocess_popen output
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]
    assert "pytest" in cmd
    assert f"{test_file}::test_pass" in cmd
    assert "--verbose" not in cmd
    assert "--cov" not in cmd
    assert "PYTEST_ADDOPTS" not in env


@pytest.mark.fast
def test_run_tests_verbose_and_report(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests with verbose and report flags."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_pass(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )
    monkeypatch.setattr(
        rt, "_ensure_coverage_artifacts", lambda: None
    )  # Prevent actual artifact generation
    monkeypatch.setattr(
        rt, "enforce_coverage_threshold", lambda *args, **kwargs: 90.0
    )  # Mock coverage enforcement
    custom_env = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}  # Enable plugin injection
    success, output = rt.run_tests(
        target="unit-tests", verbose=True, report=True, env=custom_env
    )

    assert success is True
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]
    assert "-v" in cmd
    assert f"--cov={rt.COVERAGE_TARGET}" in cmd
    assert f"--cov-report=json:{rt.COVERAGE_JSON_PATH}" in cmd
    assert f"--cov-report=html:{rt.COVERAGE_HTML_DIR}" in cmd
    assert "--cov-append" in cmd
    assert "PYTEST_ADDOPTS" in env  # Should contain plugin injection
    del os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]  # Clean up env


@pytest.mark.fast
def test_run_tests_with_markers_and_keyword_filter(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests with extra_marker and keyword_filter."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_pass(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    success, output = rt.run_tests(
        target="unit-tests", extra_marker="slow", keyword_filter="example"
    )

    assert success is True
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]
    assert "-m" in cmd
    assert "not memory_intensive and (slow)" in cmd
    assert "-k" in cmd
    assert "example" in cmd


@pytest.mark.fast
def test_run_tests_with_maxfail(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests with maxfail parameter."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_pass(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    success, output = rt.run_tests(target="unit-tests", maxfail=5)

    assert success is True
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]
    assert "--maxfail" in cmd
    assert "5" in cmd


@pytest.mark.fast
def test_run_tests_with_custom_env(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests with custom environment variables."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_pass(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    custom_env = {
        "MY_VAR": "123",
        "ANOTHER_VAR": "abc",
        "PYTEST_ADDOPTS": "",
    }  # Add PYTEST_ADDOPTS to custom_env
    success, output = rt.run_tests(target="unit-tests", env=custom_env)

    assert success is True
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]
    assert env["MY_VAR"] == "123"
    assert env["ANOTHER_VAR"] == "abc"
    # Ensure existing PYTEST_ADDOPTS are merged, not overwritten
    assert "PYTEST_ADDOPTS" in env


@pytest.mark.fast
def test_run_tests_collection_failure_returns_false(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests returns False on test collection failure."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))

    def failing_collect(target, speed_category):
        raise RuntimeError("Collection failed")

    monkeypatch.setattr(rt, "collect_tests_with_cache", failing_collect)

    success, output = rt.run_tests(target="unit-tests")

    assert success is False
    assert output == "Test collection failed"
    assert not mock_subprocess_popen  # No tests should be run


@pytest.mark.fast
def test_run_tests_no_tests_collected_returns_true_with_message(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests returns True and message when no tests are collected."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))

    monkeypatch.setattr(
        rt, "collect_tests_with_cache", lambda target, speed_category: []
    )

    success, output = rt.run_tests(target="unit-tests")

    assert success is True
    assert "No tests collected" in output
    assert not mock_subprocess_popen  # No tests should be run


@pytest.mark.fast
def test_run_tests_execution_failure_returns_false(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests returns False on test execution failure."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_fail(): assert False")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_fail"],
    )

    class FakePopenFail(rt.subprocess.Popen):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.returncode = 1  # Simulate failure

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopenFail)

    success, output = rt.run_tests(target="unit-tests")

    assert success is False
    assert "Troubleshooting tips" in output  # Should include failure tips
    assert len(mock_subprocess_popen) == 1


@pytest.mark.fast
def test_run_tests_segmented_execution(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests with segmented execution."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_a = tmp_path / "test_a.py"
    test_b = tmp_path / "test_b.py"
    test_c = tmp_path / "test_c.py"
    test_a.write_text("def test_a(): pass")
    test_b.write_text("def test_b(): pass")
    test_c.write_text("def test_c(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [
            f"{test_a}::test_a",
            f"{test_b}::test_b",
            f"{test_c}::test_c",
        ],
    )

    # Mock Popen to return success for all batches
    class FakePopenSuccess(rt.subprocess.Popen):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            # Append to the fixture's recorded_calls
            mock_subprocess_popen.append((args[0], kwargs.get("env", {})))
            super().__init__(*args, **kwargs)
            self.returncode = 0
            self._stdout = "ok"
            self._stderr = ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopenSuccess)

    success, output = rt.run_tests(target="unit-tests", segment=True, segment_size=1)

    assert success is True
    assert len(mock_subprocess_popen) == 3  # Three batches
    assert f"{test_a}::test_a" in mock_subprocess_popen[0][0]
    assert f"{test_b}::test_b" in mock_subprocess_popen[1][0]
    assert f"{test_c}::test_c" in mock_subprocess_popen[2][0]


@pytest.mark.fast
def test_run_tests_segmented_execution_with_failure(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests with segmented execution where one batch fails."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_a = tmp_path / "test_a.py"
    test_b = tmp_path / "test_b.py"
    test_a.write_text("def test_a(): pass")
    test_b.write_text("def test_b(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [
            f"{test_a}::test_a",
            f"{test_b}::test_b",
        ],
    )

    # Mock Popen to simulate failure in the first batch
    class FakePopenMixed(rt.subprocess.Popen):
        call_count = 0

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            # Append to the fixture's recorded_calls
            mock_subprocess_popen.append((args[0], kwargs.get("env", {})))
            super().__init__(*args, **kwargs)
            FakePopenMixed.call_count += 1
            if FakePopenMixed.call_count == 1:
                self.returncode = 1  # Fail first batch
                self._stdout = "fail"
                self._stderr = "error"
            else:
                self.returncode = 0
                self._stdout = "ok"
                self._stderr = ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopenMixed)

    success, output = rt.run_tests(target="unit-tests", segment=True, segment_size=1)

    assert success is False
    assert "Troubleshooting tips" in output  # Should include failure tips
    assert len(mock_subprocess_popen) == 2  # Both batches should run
    assert "fail" in output
    assert "error" in output


@pytest.mark.fast
def test_run_tests_parallel_execution(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test run_tests with parallel execution."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_pass(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    success, output = rt.run_tests(target="unit-tests", parallel=True)

    assert success is True
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]
    assert "-n auto" in cmd  # Should add parallel flag
    assert f"{test_file}::test_pass" in cmd


@pytest.mark.fast
def test_run_tests_parallel_execution_disabled_by_segment(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test parallel execution is disabled when segment is True."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_pass(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    success, output = rt.run_tests(target="unit-tests", parallel=True, segment=True)

    assert success is True
    assert len(mock_subprocess_popen) == 1  # Only one batch due to segment=True
    cmd, env = mock_subprocess_popen[0]
    assert "-n auto" not in cmd  # Parallel should be disabled
    assert [f"{test_file}::test_pass"] == cmd[
        3:
    ]  # Check if node_ids are correctly passed


@pytest.mark.fast
def test_run_tests_with_env_var_propagation(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Set some initial environment variables
    os.environ["EXISTING_VAR"] = "initial_value"
    os.environ["PYTEST_ADDOPTS"] = "-q"

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    custom_env = {"NEW_VAR": "new_value", "PYTEST_ADDOPTS": "--strict-markers"}

    success, output = rt.run_tests(target="unit-tests", env=custom_env)

    assert success is True
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]

    assert env["EXISTING_VAR"] == "initial_value"  # Existing var should be propagated
    assert env["NEW_VAR"] == "new_value"  # New var should be added
    assert (
        "-q --strict-markers" in env["PYTEST_ADDOPTS"]
    )  # PYTEST_ADDOPTS should be merged

    # Clean up os.environ
    del os.environ["EXISTING_VAR"]
    del os.environ["PYTEST_ADDOPTS"]


@pytest.mark.fast
def test_run_tests_with_no_target_path_raises_error(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that calling run_tests with an unknown target raises an error."""
    with pytest.raises(ValueError, match="Unknown test target"):
        rt.run_tests(target="non-existent-target")

    assert not mock_subprocess_run
    assert not mock_subprocess_popen


@pytest.mark.fast
def test_run_tests_with_empty_speed_categories_uses_all(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    success, output = rt.run_tests(target="unit-tests", speed_categories=[])

    assert success is True
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]
    # Should not have any -m flags for speed categories
    assert "-m" in cmd
    assert "not memory_intensive" in cmd
    assert f"{test_file}::test_pass" in cmd


@pytest.mark.fast
def test_run_tests_with_specific_speed_categories(
    tmp_path: Path,
    mock_subprocess_run: list[list[str]],
    mock_subprocess_popen: list[tuple[list[str], dict[str, str]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that specific speed_categories are correctly applied."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_pass(): pass")

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda target, speed_category: [f"{test_file}::test_pass"],
    )

    success, output = rt.run_tests(
        target="unit-tests", speed_categories=["fast", "medium"]
    )

    assert success is True
    assert len(mock_subprocess_popen) == 1
    cmd, env = mock_subprocess_popen[0]
    assert "-m" in cmd
    assert "not memory_intensive and (fast or medium)" in cmd
    assert f"{test_file}::test_pass" in cmd
