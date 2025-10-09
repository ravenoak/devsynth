"""Segmented run coverage for report flag transitions."""

from __future__ import annotations

import pytest

import devsynth.testing.run_tests as rt

from .run_tests_test_utils import build_batch_metadata


@pytest.mark.fast
def test_run_segmented_tests_reports_only_last_segment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only the final segment should request coverage reports."""

    report_flags: list[bool] = []

    def fake_run_single_test_batch(
        config: rt.SingleBatchRequest,
    ) -> rt.BatchExecutionResult:
        node_ids = list(config.node_ids)
        report_flags.append(config.report)
        return (
            True,
            f"segment {len(report_flags)} ok ({len(node_ids)} tests)",
            build_batch_metadata(
                f"batch-report-{len(report_flags)}", command=["pytest"], returncode=0
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
    assert metadata["segments"][-1]["metadata_id"].startswith("batch-report-")
