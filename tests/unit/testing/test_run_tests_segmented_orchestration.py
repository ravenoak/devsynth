"""Regression coverage for segmented orchestration in ``run_tests``."""

from __future__ import annotations

from typing import Any

import pytest

import devsynth.testing.run_tests as rt

from .run_tests_test_utils import build_batch_metadata, build_segment_metadata


def _collect_two_nodes(*_args: Any, **_kwargs: Any) -> list[str]:
    return [
        "tests/unit/test_alpha.py::test_one",
        "tests/unit/test_beta.py::test_two",
    ]


@pytest.mark.fast
def test_run_tests_segmented_success_invokes_publish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Successful segmented runs surface combined output and metadata."""

    monkeypatch.setattr(rt, "collect_tests_with_cache", _collect_two_nodes)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    publication_calls: list[dict[str, object]] = []

    def fake_publish(**kwargs: object) -> None:
        publication_calls.append(kwargs)
        return None

    monkeypatch.setattr(rt, "_maybe_publish_coverage_evidence", fake_publish)

    def fake_segmented(request: rt.SegmentedRunRequest) -> rt.SegmentedRunResult:
        assert isinstance(request, rt.SegmentedRunRequest)
        assert request.segment_size == 2
        metadata = build_segment_metadata(
            "seg-success",
            segments=[
                build_batch_metadata("batch-a"),
                build_batch_metadata("batch-b"),
            ],
        )
        return True, "segment ok", metadata

    monkeypatch.setattr(rt, "_run_segmented_tests", fake_segmented)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        segment_size=2,
        report=False,
        verbose=False,
        parallel=False,
    )

    assert success is True
    assert output == "segment ok"
    assert publication_calls and publication_calls[0]["report"] is False


@pytest.mark.fast
def test_run_tests_segmented_failure_skips_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failed segmented runs propagate failures without graph publication messages."""

    monkeypatch.setattr(rt, "collect_tests_with_cache", _collect_two_nodes)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    publish_calls: list[dict[str, object]] = []

    def fake_publish(**kwargs: object) -> None:
        publish_calls.append(kwargs)
        return None

    monkeypatch.setattr(rt, "_maybe_publish_coverage_evidence", fake_publish)

    def fake_segmented(_: rt.SegmentedRunRequest) -> rt.SegmentedRunResult:
        metadata = build_segment_metadata(
            "seg-failure",
            segments=[build_batch_metadata("batch-fail", returncode=2)],
            returncode=2,
        )
        return False, "segment fail", metadata

    monkeypatch.setattr(rt, "_run_segmented_tests", fake_segmented)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        segment_size=5,
        report=True,
        verbose=False,
        parallel=False,
    )

    assert success is False
    assert output == "segment fail"
    assert publish_calls and publish_calls[0]["success"] is False


@pytest.mark.fast
def test_run_tests_segmented_reports_append_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When graph publication succeeds the message is appended to stdout."""

    monkeypatch.setattr(rt, "collect_tests_with_cache", _collect_two_nodes)
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def fake_segmented(_: rt.SegmentedRunRequest) -> rt.SegmentedRunResult:
        metadata = build_segment_metadata(
            "seg-graph",
            segments=[build_batch_metadata("batch-graph")],
        )
        return True, "segment done", metadata

    monkeypatch.setattr(rt, "_run_segmented_tests", fake_segmented)

    def fake_publish(**_: object) -> str:
        return "[knowledge-graph] published run=abc123"

    monkeypatch.setattr(rt, "_maybe_publish_coverage_evidence", fake_publish)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        segment_size=3,
        report=True,
        verbose=False,
        parallel=False,
    )

    assert success is True
    assert output.endswith("[knowledge-graph] published run=abc123\n")
