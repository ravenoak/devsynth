"""Unit tests for deterministic coverage segmentation simulations.

Issue: issues/coverage-below-threshold.md ReqID: COV-SEG-001
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import pytest


def _simulate_segments(
    total_lines: int, segments: Sequence[Iterable[int]]
) -> list[float]:
    """Return cumulative coverage percentages after each segment."""

    covered: set[int] = set()
    coverage_history: list[float] = []
    for executed in segments:
        covered.update(executed)
        coverage_history.append(len(covered) / total_lines)
    return coverage_history


def _segments_to_threshold(
    total_lines: int, segments: Sequence[Iterable[int]], threshold: float
) -> tuple[int | None, list[float]]:
    """Return the segment index that first meets ``threshold`` and the history."""

    history = _simulate_segments(total_lines, segments)
    for index, coverage in enumerate(history, start=1):
        if coverage >= threshold:
            return index, history
    return None, history


@pytest.mark.fast
def test_segment_union_reaches_threshold_with_overlap():
    """ReqID: COV-SEG-001 — Overlapping segments still reach the 90% target."""

    total_lines = 100
    segments = [range(0, 60), range(40, 90), range(80, 100)]

    history = _simulate_segments(total_lines, segments)

    assert history == pytest.approx([0.60, 0.90, 1.0])
    assert history[-1] >= 0.90
    assert history == sorted(history), "coverage must be monotonic non-decreasing"


@pytest.mark.fast
def test_segment_threshold_detection_matches_cli_expectations():
    """ReqID: COV-SEG-001 — Three CLI segments can guarantee ≥90% aggregate coverage."""

    total_lines = 180
    segments = [range(0, 70), range(55, 125), range(110, 180)]

    threshold_index, history = _segments_to_threshold(total_lines, segments, 0.90)

    assert threshold_index == 3
    assert history[threshold_index - 1] >= 0.90
    assert history == sorted(history)
