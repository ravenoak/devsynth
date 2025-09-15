"""Tests for :mod:`devsynth.consensus`.

ReqID: CONSENSUS-01; Issue: issues/consensus-building.md
"""

from __future__ import annotations

import pytest

from devsynth.consensus import build_consensus

pytestmark = [pytest.mark.unit, pytest.mark.fast]


def test_build_consensus_majority() -> None:
    """ReqID: CONSENSUS-01; Issue: issues/consensus-building.md"""
    result = build_consensus(["a", "a", "b"])
    assert result.consensus is True
    assert result.decision == "a"
    assert result.counts["a"] == 2
    assert pytest.approx(result.ratio, rel=1e-6) == 2 / 3


def test_build_consensus_no_consensus() -> None:
    """ReqID: CONSENSUS-01; Issue: issues/consensus-building.md"""
    result = build_consensus(["a", "b"], threshold=0.6)
    assert result.consensus is False
    assert result.decision is None
    assert set(result.dissenting or []) == {"a", "b"}


def test_build_consensus_invalid_threshold() -> None:
    """ReqID: CONSENSUS-01; Issue: issues/consensus-building.md"""
    with pytest.raises(ValueError):
        build_consensus(["a"], threshold=0)


def test_build_consensus_empty_votes() -> None:
    """ReqID: CONSENSUS-01; Issue: issues/consensus-building.md"""
    with pytest.raises(ValueError):
        build_consensus([])
