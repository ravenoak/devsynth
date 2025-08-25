"""Lightweight performance smoke tests for critical paths.

These are designed to be fast and stable across CI. They act as guardrails
rather than precise benchmarks, aligning with docs/tasks.md item 20.103.
"""

from __future__ import annotations

import time
from typing import Any, Dict

import pytest

from devsynth.domain.models.requirement import Requirement
from devsynth.domain.models.wsde_dialectical import _prioritize_critiques
from devsynth.domain.models.wsde_facade import WSDETeam


@pytest.mark.fast
def test_benchmark_requirements_update_speed():
    # Create a handful of requirements and perform updates quickly
    reqs = [Requirement(title=f"R{i}", description="desc") for i in range(20)]

    start = time.perf_counter()
    for r in reqs:
        r.update(description=r.description + "!")
    elapsed = time.perf_counter() - start

    # Generous upper bound to remain stable on CI
    assert elapsed < 0.25, f"Requirement updates too slow: {elapsed:.3f}s"


class _PerfTeam(WSDETeam):
    def __init__(self):
        super().__init__(name="PerfTeam")


@pytest.mark.fast
@pytest.mark.no_network
def test_benchmark_dialectical_prioritization_speed_simple_input():
    team = _PerfTeam()
    critiques = [
        "Critical performance issue in algorithm",
        "Minor readability concern",
        "Security vulnerability potential",
        "Usability could be improved",
    ]

    start = time.perf_counter()
    result = _prioritize_critiques(team, critiques)
    elapsed = time.perf_counter() - start

    assert (
        isinstance(result, list) and result
    ), "Prioritization should return a non-empty list"
    assert elapsed < 0.4, f"Prioritization too slow for trivial input: {elapsed:.3f}s"
