from __future__ import annotations

import os
from collections.abc import Iterator
from typing import assert_type

import pytest

from devsynth.testing import run_tests as run_tests_module

from .run_tests_test_utils import build_batch_metadata


@pytest.mark.fast
def test_run_tests_segmented_failure_surfaces_remediation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Segmented runs aggregate failure logs and remediation hints."""

    monkeypatch.setattr(run_tests_module, "_reset_coverage_artifacts", lambda: None)
    ensure_calls: list[None] = []
    monkeypatch.setattr(
        run_tests_module,
        "_ensure_coverage_artifacts",
        lambda: ensure_calls.append(None),
    )

    collected = [
        "tests/unit/test_alpha.py::test_one",
        "tests/unit/test_beta.py::test_two",
        "tests/unit/test_gamma.py::test_three",
    ]
    monkeypatch.setattr(
        run_tests_module,
        "collect_tests_with_cache",
        lambda target, speed: list(collected),
    )

    batches: list[list[str]] = []

    def fake_run_single(
        config: run_tests_module.SingleBatchRequest,
    ) -> run_tests_module.BatchExecutionResult:
        assert_type(config, run_tests_module.SingleBatchRequest)
        node_ids = list(config.node_ids)
        batches.append(node_ids)
        cmd = ["python", "-m", "pytest", *node_ids]
        tips = run_tests_module._failure_tips(2 + len(batches), cmd)
        return (
            False,
            f"segment-{len(batches)} failed\n{tips}",
            build_batch_metadata(
                f"batch-failure-{len(batches)}",
                command=cmd,
                returncode=2 + len(batches),
            ),
        )

    monkeypatch.setattr(run_tests_module, "_run_single_test_batch", fake_run_single)

    success, output = run_tests_module.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=2,
        maxfail=None,
    )

    assert batches == [
        ["tests/unit/test_alpha.py::test_one", "tests/unit/test_beta.py::test_two"],
        ["tests/unit/test_gamma.py::test_three"],
    ]
    assert not success
    assert output.count("Pytest exited with code") == 2
    assert "- Segment large suites to localize failures" in output
    assert ensure_calls, "_ensure_coverage_artifacts should run after segmentation"


@pytest.mark.fast
def test__run_segmented_tests_aggregates_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Segment helper preserves order and troubleshooting tips across batches."""

    outputs: list[run_tests_module.BatchExecutionResult] = [
        (
            True,
            "segment-1 passed",
            build_batch_metadata(
                "batch-1",
                command=["python", "segment-1", "tests/unit/test_alpha.py::test_one"],
                returncode=0,
            ),
        ),
        (
            False,
            "segment-2 failed\n"
            + run_tests_module._failure_tips(
                3, ["python", "-m", "pytest", "tests/unit/test_gamma.py::test_three"]
            ),
            build_batch_metadata(
                "batch-2",
                command=["python", "segment-2", "tests/unit/test_gamma.py::test_three"],
                returncode=3,
            ),
        ),
    ]
    call_iter: Iterator[run_tests_module.BatchExecutionResult] = iter(outputs)

    def fake_run_single(
        config: run_tests_module.SingleBatchRequest,
    ) -> run_tests_module.BatchExecutionResult:
        assert_type(config, run_tests_module.SingleBatchRequest)
        return next(call_iter)

    ensure_calls: list[None] = []
    monkeypatch.setattr(run_tests_module, "_run_single_test_batch", fake_run_single)
    monkeypatch.setattr(
        run_tests_module,
        "_ensure_coverage_artifacts",
        lambda: ensure_calls.append(None),
    )

    segmented_request = run_tests_module.SegmentedRunRequest(
        target="unit-tests",
        speed_categories=("fast",),
        marker_expr="(fast)",
        node_ids=(
            "tests/unit/test_alpha.py::test_one",
            "tests/unit/test_beta.py::test_two",
            "tests/unit/test_gamma.py::test_three",
        ),
        verbose=False,
        report=False,
        parallel=False,
        segment_size=2,
        maxfail=None,
        keyword_filter=None,
        env={},
    )

    success, output, metadata = run_tests_module._run_segmented_tests(segmented_request)

    assert not success
    assert "segment-1 passed" in output
    assert "segment-2 failed" in output
    assert output.count("Pytest exited with code") == 1
    assert ensure_calls, "_ensure_coverage_artifacts should run after helper"
    assert_type(metadata, run_tests_module.SegmentedRunMetadata)
    assert metadata["metadata_id"].startswith("segmented-")
    assert isinstance(metadata["commands"], tuple)
    assert all(isinstance(command, tuple) for command in metadata["commands"])
    assert isinstance(metadata["segments"], tuple)
    assert metadata["commands"] == (
        ("python", "segment-1", "tests/unit/test_alpha.py::test_one"),
        ("python", "segment-2", "tests/unit/test_gamma.py::test_three"),
    )
    assert [segment["metadata_id"] for segment in metadata["segments"]] == [
        "batch-1",
        "batch-2",
    ]
    for segment, command in zip(
        metadata["segments"], metadata["commands"], strict=True
    ):
        assert_type(segment, run_tests_module.BatchExecutionMetadata)
        assert isinstance(segment["command"], tuple)
        assert segment["command"] == command


@pytest.mark.fast
def test_segmented_runs_reinject_plugins_without_clobbering_addopts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Segmentation preserves caller addopts while reinjecting coverage plugins."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k smoke")

    monkeypatch.setattr(run_tests_module, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(run_tests_module, "_ensure_coverage_artifacts", lambda: None)

    node_ids = [
        "tests/unit/test_alpha.py::test_one",
        "tests/unit/test_beta.py::test_two",
    ]
    monkeypatch.setattr(
        run_tests_module,
        "collect_tests_with_cache",
        lambda target, speed: list(node_ids),
    )

    snapshots: list[str] = []

    def fake_run_single(
        config: run_tests_module.SingleBatchRequest,
    ) -> run_tests_module.BatchExecutionResult:
        assert_type(config, run_tests_module.SingleBatchRequest)
        snapshots.append(config.env.get("PYTEST_ADDOPTS", ""))
        node_ids_local = list(config.node_ids)
        return (
            True,
            f"segment for {node_ids_local[0]}",
            build_batch_metadata(
                f"batch-smoke-{node_ids_local[0]}", command=["pytest"], returncode=0
            ),
        )

    monkeypatch.setattr(run_tests_module, "_run_single_test_batch", fake_run_single)

    success, output = run_tests_module.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=None,
    )

    assert success
    assert output.count("segment for") == len(node_ids)
    assert os.environ["PYTEST_ADDOPTS"] == "-k smoke"
    expected_suffix = "-p pytest_asyncio.plugin -k smoke -p pytest_cov -p pytest_bdd.plugin"
    assert snapshots == [expected_suffix, expected_suffix]


@pytest.mark.fast
def test_run_tests_single_batch_uses_request_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Single-batch runs provide typed requests to the execution helper."""

    monkeypatch.setattr(run_tests_module, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(run_tests_module, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(
        run_tests_module, "pytest_cov_support_status", lambda env: (True, None)
    )
    monkeypatch.setattr(
        run_tests_module, "ensure_pytest_cov_plugin_env", lambda env: True
    )
    monkeypatch.setattr(
        run_tests_module, "ensure_pytest_bdd_plugin_env", lambda env: True
    )
    monkeypatch.setattr(
        run_tests_module,
        "_maybe_publish_coverage_evidence",
        lambda **_kwargs: "",
    )

    collected = ["tests/unit/test_delta.py::test_single"]
    monkeypatch.setattr(
        run_tests_module,
        "collect_tests_with_cache",
        lambda *_args, **_kwargs: list(collected),
    )

    captured_requests: list[run_tests_module.SingleBatchRequest] = []

    def fake_run_single(
        config: run_tests_module.SingleBatchRequest,
    ) -> run_tests_module.BatchExecutionResult:
        assert isinstance(config, run_tests_module.SingleBatchRequest)
        captured_requests.append(config)
        return True, "batch ok", build_batch_metadata("batch-single")

    monkeypatch.setattr(run_tests_module, "_run_single_test_batch", fake_run_single)

    success, output = run_tests_module.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
    )

    assert success is True
    assert output == "batch ok"
    assert len(captured_requests) == 1
    request = captured_requests[0]
    assert request.node_ids == tuple(collected)
    assert request.marker_expr == "not memory_intensive and fast and not gui"
    assert request.parallel is False
    assert request.report is False
