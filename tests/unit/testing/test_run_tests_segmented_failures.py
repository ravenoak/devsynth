from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from devsynth.testing import run_tests as run_tests_module


@pytest.mark.fast
def test_run_tests_segmented_failure_surfaces_remediation(monkeypatch: pytest.MonkeyPatch) -> None:
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
    ) -> tuple[bool, str, dict[str, object]]:
        node_ids = list(config.node_ids)
        batches.append(node_ids)
        cmd = ["python", "-m", "pytest", *node_ids]
        tips = run_tests_module._failure_tips(2 + len(batches), cmd)
        return (
            False,
            f"segment-{len(batches)} failed\n{tips}",
            {
                "metadata_id": f"batch-failure-{len(batches)}",
                "command": cmd,
                "returncode": 2 + len(batches),
                "started_at": "start",
                "completed_at": "end",
            },
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
def test__run_segmented_tests_aggregates_outputs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Segment helper preserves order and troubleshooting tips across batches."""

    outputs = [
        (
            True,
            "segment-1 passed",
            {"metadata_id": "batch-1", "command": ["pytest"], "returncode": 0},
        ),
        (
            False,
            "segment-2 failed\n"
            + run_tests_module._failure_tips(
                3, ["python", "-m", "pytest", "tests/unit/test_gamma.py::test_three"]
            ),
            {
                "metadata_id": "batch-2",
                "command": ["pytest"],
                "returncode": 3,
                "started_at": "start",
                "completed_at": "end",
            },
        ),
    ]
    call_iter: Iterator[tuple[bool, str, dict[str, object]]] = iter(outputs)

    def fake_run_single(
        config: run_tests_module.SingleBatchRequest,
    ) -> tuple[bool, str, dict[str, object]]:
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
    assert isinstance(metadata.get("metadata_id"), str)
    segment_ids = [segment.get("metadata_id") for segment in metadata.get("segments", [])]
    assert len(segment_ids) == len(set(segment_ids))


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
    ) -> tuple[bool, str, dict[str, object]]:
        snapshots.append(config.env.get("PYTEST_ADDOPTS", ""))
        node_ids_local = list(config.node_ids)
        return (
            True,
            f"segment for {node_ids_local[0]}",
            {
                "metadata_id": f"batch-smoke-{node_ids_local[0]}",
                "command": ["pytest"],
                "returncode": 0,
                "started_at": "start",
                "completed_at": "end",
            },
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
    expected_suffix = "-k smoke -p pytest_cov -p pytest_bdd.plugin"
    assert snapshots == [expected_suffix, expected_suffix]
