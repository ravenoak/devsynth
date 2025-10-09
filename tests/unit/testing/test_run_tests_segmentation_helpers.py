"""Targeted coverage tests for segmentation helper functions."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import assert_type
from unittest.mock import MagicMock, patch

import pytest

import devsynth.testing.run_tests as rt

from .run_tests_test_utils import build_batch_metadata


@pytest.mark.fast
def test_run_segmented_tests_single_speed(monkeypatch):
    """ReqID: RUN-TESTS-SEG-1 — _run_segmented_tests handles single speed category."""

    segment_outputs: list[str] = []

    def fake_single_batch(
        config: rt.SingleBatchRequest,
    ) -> rt.BatchExecutionResult:
        segment_outputs.append(" ".join(config.node_ids))
        return (
            True,
            f"Batch output for: {list(config.node_ids)[0][:20]}...",
            build_batch_metadata("batch-helper-1", command=["pytest"], returncode=0),
        )

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_single_batch)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    request = rt.SegmentedRunRequest(
        target="unit-tests",
        speed_categories=("fast",),
        marker_expr="fast and not memory_intensive",
        node_ids=(
            "test1.py::test_a",
            "test2.py::test_b",
            "test3.py::test_c",
            "test4.py::test_d",
        ),
        verbose=False,
        report=True,
        parallel=False,
        segment_size=2,
        maxfail=None,
        keyword_filter=None,
        env={},
    )

    success, output, metadata = rt._run_segmented_tests(request)

    assert success is True
    assert "Batch output for:" in output
    assert metadata["commands"]
    assert segment_outputs == [
        "test1.py::test_a test2.py::test_b",
        "test3.py::test_c test4.py::test_d",
    ]


@pytest.mark.fast
def test_run_segmented_tests_multiple_speeds(monkeypatch):
    """ReqID: RUN-TESTS-SEG-2 — handles multiple speed categories."""

    def fake_single_batch(
        config: rt.SingleBatchRequest,
    ) -> rt.BatchExecutionResult:
        node_text = "|".join(config.node_ids)
        return True, f"Batch for {node_text}", build_batch_metadata(node_text)

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_single_batch)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    request = rt.SegmentedRunRequest(
        target="unit-tests",
        speed_categories=("fast", "medium"),
        marker_expr="(fast or medium) and not memory_intensive",
        node_ids=("test1.py::test_fast", "test2.py::test_medium"),
        verbose=False,
        report=False,
        parallel=False,
        segment_size=1,
        maxfail=None,
        keyword_filter=None,
        env={},
    )

    success, output, metadata = rt._run_segmented_tests(request)

    assert success is True
    assert "test1.py::test_fast" in output
    assert "test2.py::test_medium" in output
    assert {segment["metadata_id"] for segment in metadata["segments"]} == {
        "test1.py::test_fast",
        "test2.py::test_medium",
    }


@pytest.mark.fast
def test_run_segmented_tests_no_tests_found(monkeypatch):
    """ReqID: RUN-TESTS-SEG-3 — _run_segmented_tests handles no tests found."""

    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    request = rt.SegmentedRunRequest(
        target="unit-tests",
        speed_categories=("fast",),
        marker_expr="fast and not memory_intensive",
        node_ids=(),
        verbose=False,
        report=False,
        parallel=False,
        segment_size=2,
        maxfail=None,
        keyword_filter=None,
        env={},
    )

    success, output, metadata = rt._run_segmented_tests(request)

    assert success is True
    assert output == ""
    assert metadata["segments"] == []


@pytest.mark.fast
def test_run_segmented_tests_failure_with_maxfail(monkeypatch):
    """ReqID: RUN-TESTS-SEG-4 — _run_segmented_tests stops on failure with maxfail."""

    call_count = 0

    def fake_single_batch(
        config: rt.SingleBatchRequest,
    ) -> rt.BatchExecutionResult:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return (
                False,
                "First segment failed",
                build_batch_metadata("batch-fail-1", returncode=1),
            )
        return True, "Should not be called", build_batch_metadata("batch-fail-2")

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_single_batch)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    request = rt.SegmentedRunRequest(
        target="unit-tests",
        speed_categories=("fast",),
        marker_expr="fast and not memory_intensive",
        node_ids=(
            "test1.py::test_a",
            "test2.py::test_b",
            "test3.py::test_c",
            "test4.py::test_d",
        ),
        verbose=False,
        report=False,
        parallel=False,
        segment_size=2,
        maxfail=1,
        keyword_filter=None,
        env={},
    )

    success, output, metadata = rt._run_segmented_tests(request)

    assert success is False
    assert "First segment failed" in output
    assert call_count == 1  # Should stop after first failure
    assert metadata["segments"][0]["metadata_id"] == "batch-fail-1"


@pytest.mark.fast
def test_collect_tests_with_cache_all_tests_decomposes_successfully(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """ReqID: RUN-TESTS-SEG-6 — all-tests decomposes into dependent targets on miss."""

    cache_dir = tmp_path / ".cache"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", cache_dir)
    monkeypatch.setattr(
        rt, "TEST_COLLECTION_CACHE_FILE", cache_dir / "collection_cache.json"
    )

    tests_root = tmp_path / "tests"
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"
    behavior_dir = tests_root / "behavior"
    for path in (unit_dir, integration_dir, behavior_dir):
        path.mkdir(parents=True)
        (path / "test_example.py").write_text(
            "def test_ok():\n    pass\n", encoding="utf-8"
        )

    monkeypatch.setattr(
        rt,
        "TARGET_PATHS",
        {
            "unit-tests": str(unit_dir),
            "integration-tests": str(integration_dir),
            "behavior-tests": str(behavior_dir),
            "all-tests": str(tests_root),
        },
    )

    calls: list[str] = []

    class DummyProcess:
        def __init__(self, stdout: str) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = 0

    mapping = {
        str(unit_dir): "tests/unit/test_example.py::test_ok\n",
        str(integration_dir): "tests/integration/test_example.py::test_ok\n",
        str(behavior_dir): "tests/behavior/test_example.py::test_ok\n",
    }

    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        test_path = cmd[3]
        calls.append(test_path)
        stdout = mapping.get(test_path)
        if stdout is None:
            raise AssertionError(f"Unexpected test path {test_path}")
        return DummyProcess(stdout)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    caplog.set_level(logging.INFO)

    result = rt.collect_tests_with_cache("all-tests", "fast")

    assert result == [
        "tests/unit/test_example.py::test_ok",
        "tests/integration/test_example.py::test_ok",
        "tests/behavior/test_example.py::test_ok",
    ]
    assert calls == [str(unit_dir), str(integration_dir), str(behavior_dir)]
    assert any(
        getattr(record, "event", "") == "test_collection_cache_miss"
        for record in caplog.records
    )


@pytest.mark.fast
def test_collect_tests_with_cache_timeout_falls_back_to_direct_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """ReqID: RUN-TESTS-SEG-7 — retries smaller batches before broad fallback."""

    cache_dir = tmp_path / ".cache"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", cache_dir)
    monkeypatch.setattr(
        rt, "TEST_COLLECTION_CACHE_FILE", cache_dir / "collection_cache.json"
    )

    tests_root = tmp_path / "tests"
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"
    behavior_dir = tests_root / "behavior"
    for path in (unit_dir, integration_dir, behavior_dir):
        path.mkdir(parents=True)
        (path / "test_example.py").write_text(
            "def test_ok():\n    pass\n", encoding="utf-8"
        )

    monkeypatch.setattr(
        rt,
        "TARGET_PATHS",
        {
            "unit-tests": str(unit_dir),
            "integration-tests": str(integration_dir),
            "behavior-tests": str(behavior_dir),
            "all-tests": str(tests_root),
        },
    )

    calls: list[str] = []

    class DummyProcess:
        def __init__(self, stdout: str) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = 0

    fallback_output = (
        "tests/unit/test_example.py::test_ok\n"
        "tests/integration/test_example.py::test_ok\n"
        "tests/behavior/test_example.py::test_ok\n"
    )

    timeout_targets = {str(unit_dir), str(integration_dir), str(behavior_dir)}

    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        test_path = cmd[3]
        calls.append(test_path)
        if test_path in timeout_targets:
            raise subprocess.TimeoutExpired(cmd, timeout)
        if test_path == str(tests_root):
            return DummyProcess(fallback_output)
        raise AssertionError(f"Unexpected test path {test_path}")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    caplog.set_level(logging.INFO)

    result = rt.collect_tests_with_cache("all-tests", "fast")

    assert result == [
        "tests/unit/test_example.py::test_ok",
        "tests/integration/test_example.py::test_ok",
        "tests/behavior/test_example.py::test_ok",
    ]
    assert calls[-1] == str(tests_root)
    assert any(
        getattr(record, "event", "") == "test_collection_timeout_retry"
        for record in caplog.records
    )


@pytest.mark.fast
def test_collect_tests_with_cache_reuses_cache_and_preserves_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """ReqID: RUN-TESTS-SEG-8 — cache hits keep env stable without subprocess reruns."""

    cache_dir = tmp_path / ".cache"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", cache_dir)
    monkeypatch.setattr(
        rt, "TEST_COLLECTION_CACHE_FILE", cache_dir / "collection_cache.json"
    )

    tests_root = tmp_path / "tests"
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"
    behavior_dir = tests_root / "behavior"
    for path in (unit_dir, integration_dir, behavior_dir):
        path.mkdir(parents=True)
        (path / "test_example.py").write_text(
            "def test_ok():\n    pass\n", encoding="utf-8"
        )

    monkeypatch.setattr(
        rt,
        "TARGET_PATHS",
        {
            "unit-tests": str(unit_dir),
            "integration-tests": str(integration_dir),
            "behavior-tests": str(behavior_dir),
            "all-tests": str(tests_root),
        },
    )

    class DummyProcess:
        def __init__(self, stdout: str) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = 0

    fallback_output = (
        "tests/unit/test_example.py::test_ok\n"
        "tests/integration/test_example.py::test_ok\n"
        "tests/behavior/test_example.py::test_ok\n"
    )

    def fake_run(cmd, capture_output, text, timeout):  # type: ignore[no-untyped-def]
        return DummyProcess(fallback_output)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    caplog.set_level(logging.INFO)

    first = rt.collect_tests_with_cache("all-tests", "fast")
    assert first == [
        "tests/unit/test_example.py::test_ok",
        "tests/integration/test_example.py::test_ok",
        "tests/behavior/test_example.py::test_ok",
    ]

    def fail_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("subprocess.run should not be called on cache hit")

    monkeypatch.setattr(rt.subprocess, "run", fail_run)

    monkeypatch.setenv("DEVSYNTH_TEST_COLLECTION_TIMEOUT_SECONDS", "123")
    env_snapshot = dict(os.environ)

    second = rt.collect_tests_with_cache("all-tests", "fast")
    assert second == first
    assert os.environ["DEVSYNTH_TEST_COLLECTION_TIMEOUT_SECONDS"] == "123"
    assert dict(os.environ) == env_snapshot
    assert any(
        getattr(record, "event", "") == "test_collection_cache_hit"
        for record in caplog.records
    )


@pytest.mark.fast
def test_run_segmented_tests_dry_run_batches_use_typed_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: RUN-TESTS-SEG-5 — dry-run segments propagate typed requests."""

    ensure_calls: list[None] = []
    monkeypatch.setattr(
        rt, "_ensure_coverage_artifacts", lambda: ensure_calls.append(None)
    )

    captured_batches: list[rt.SingleBatchRequest] = []

    def fake_single_batch(
        config: rt.SingleBatchRequest,
    ) -> rt.BatchExecutionResult:
        assert_type(config, rt.SingleBatchRequest)
        captured_batches.append(config)
        assert config.dry_run is True
        return (
            True,
            f"Dry-run batch for {list(config.node_ids)}",
            build_batch_metadata(
                f"batch-dry-{len(captured_batches)}",
                command=["pytest"],
                returncode=0,
                dry_run=True,
            ),
        )

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_single_batch)

    env: dict[str, str] = {}
    request = rt.SegmentedRunRequest(
        target="unit-tests",
        speed_categories=("fast",),
        marker_expr="fast and not memory_intensive",
        node_ids=(
            "test1.py::test_a",
            "test2.py::test_b",
            "test3.py::test_c",
        ),
        verbose=False,
        report=False,
        parallel=False,
        segment_size=2,
        maxfail=None,
        keyword_filter=None,
        env=env,
        dry_run=True,
    )

    assert_type(request, rt.SegmentedRunRequest)

    success, output, metadata = rt._run_segmented_tests(request)

    assert success is True
    assert "Dry-run batch" in output
    assert ensure_calls == []
    assert captured_batches and all(batch.dry_run for batch in captured_batches)
    assert len(metadata["segments"]) == 2


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

    request = rt.SingleBatchRequest(
        node_ids=("tests/unit/",),
        marker_expr="fast and not memory_intensive",
        verbose=True,
        report=True,
        parallel=True,
        maxfail=5,
        keyword_filter="test_something",
        env={},
    )

    success, output, metadata = rt._run_single_test_batch(request)

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
    assert metadata["metadata_id"].startswith("batch-")


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
        request = rt.SingleBatchRequest(
            node_ids=("test1.py::test_a", "test2.py::test_b"),
            marker_expr="fast",
            verbose=False,
            report=False,
            parallel=False,
            maxfail=None,
            keyword_filter=None,
            env={},
        )
        success, output, metadata = rt._run_single_test_batch(request)

    assert success is True
    assert "test1.py::test_a" in captured_cmd
    assert "test2.py::test_b" in captured_cmd
    assert metadata["metadata_id"].startswith("batch-")


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
        request = rt.SingleBatchRequest(
            node_ids=("tests/unit/",),
            marker_expr="fast",
            verbose=False,
            report=False,
            parallel=False,
            maxfail=None,
            keyword_filter=None,
            env=test_env,
        )
        success, output, metadata = rt._run_single_test_batch(request)

    assert success is True
    assert "PYTEST_ADDOPTS" in captured_env
    addopts = captured_env["PYTEST_ADDOPTS"]
    assert "--tb=short" in addopts
    assert "-p pytest_cov" in addopts
    assert "-p pytest_bdd" in addopts
    assert metadata["metadata_id"].startswith("batch-")


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
        request = rt.SingleBatchRequest(
            node_ids=("tests/unit/",),
            marker_expr="fast",
            verbose=False,
            report=False,
            parallel=False,  # Explicitly disabled
            maxfail=None,
            keyword_filter=None,
            env={},
        )
        success, output, metadata = rt._run_single_test_batch(request)

    assert success is True
    # Should not contain -n auto when parallel is False
    assert "-n" not in captured_cmd or "auto" not in captured_cmd
