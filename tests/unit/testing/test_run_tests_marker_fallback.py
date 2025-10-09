"""Regression coverage for marker fallback and segmentation bypass."""

from __future__ import annotations

from pathlib import Path

import pytest

import devsynth.testing.run_tests as rt

from .run_tests_test_utils import build_batch_metadata, build_segment_metadata


@pytest.mark.fast
def test_run_tests_marker_fallback_skips_segmentation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When no nodes match, run_tests should fall back without segmenting."""

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: False)

    monkeypatch.setattr(rt, "collect_tests_with_cache", lambda *args, **kwargs: [])

    segmented_calls: list[rt.SegmentedRunRequest] = []

    def fake_segmented(request: rt.SegmentedRunRequest) -> rt.SegmentedRunResult:
        segmented_calls.append(request)
        return True, "segment", build_segment_metadata("seg-1")

    monkeypatch.setattr(rt, "_run_segmented_tests", fake_segmented)

    batch_calls: list[list[str]] = []

    def fake_batch(request: rt.SingleBatchRequest) -> rt.BatchExecutionResult:
        batch_calls.append(list(request.node_ids))
        return True, "batch success", build_batch_metadata("batch-1")

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_batch)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        report=False,
        verbose=False,
        parallel=False,
    )

    assert success is True
    assert output.startswith("Marker fallback executed.")
    assert not segmented_calls, "segmentation should be bypassed when fallback triggers"
    assert batch_calls == [[rt.TARGET_PATHS["unit-tests"]]]
