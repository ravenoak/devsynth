"""Segmented run coverage for report flag transitions."""

from __future__ import annotations

from typing import assert_type

import pytest

import devsynth.testing.run_tests as rt

from .run_tests_test_utils import build_batch_metadata


@pytest.mark.fast
def test_run_segmented_tests_reports_only_last_segment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only the final segment should request coverage reports."""

    report_flags: list[bool] = []
    call_index = 0

    def fake_run_single_test_batch(
        config: rt.SingleBatchRequest,
    ) -> rt.BatchExecutionResult:
        nonlocal call_index
        assert_type(config, rt.SingleBatchRequest)
        node_ids = list(config.node_ids)
        call_index += 1
        report_flags.append(config.report)
        command = [
            f"python-report-{call_index}",
            *config.node_ids,
        ]
        return (
            True,
            f"segment {len(report_flags)} ok ({len(node_ids)} tests)",
            build_batch_metadata(
                f"batch-report-{len(report_flags)}",
                command=command,
                returncode=0,
            ),
        )

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single_test_batch)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    request = rt.SegmentedRunRequest(
        target="unit-tests",
        speed_categories=("fast",),
        marker_expr="fast and not memory_intensive",
        node_ids=(
            "tests/unit/test_alpha.py::test_a",
            "tests/unit/test_beta.py::test_b",
            "tests/unit/test_gamma.py::test_c",
        ),
        verbose=False,
        report=True,
        parallel=True,
        segment_size=2,
        maxfail=None,
        keyword_filter=None,
        env={},
    )

    success, output, metadata = rt._run_segmented_tests(request)

    assert success is True
    assert report_flags == [False, True]
    assert "segment 1 ok" in output
    assert "segment 2 ok" in output
    assert_type(metadata, rt.SegmentedRunMetadata)
    assert metadata["metadata_id"].startswith("segmented-")
    assert metadata["commands"] == [
        [
            "python-report-1",
            "tests/unit/test_alpha.py::test_a",
            "tests/unit/test_beta.py::test_b",
        ],
        [
            "python-report-2",
            "tests/unit/test_gamma.py::test_c",
        ],
    ]
    assert metadata["segments"][-1]["metadata_id"].startswith("batch-report-")
    assert list(metadata["segments"][-1]["command"]) == metadata["commands"][-1]
