"""Unit tests for WSDE consensus utility helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from devsynth.application.collaboration.wsde_team_consensus import (
    ConsensusBuildingMixin,
)


class DummyConsensus(ConsensusBuildingMixin):
    """Consensus mixin stub with mockable collaborators."""

    def __init__(self) -> None:
        self.logger = MagicMock()
        self.agents = []


@pytest.mark.fast
def test_opinions_conflict_detects_contradictions() -> None:
    mixin = DummyConsensus()
    assert mixin._opinions_conflict("Yes, proceed", "No, stop")
    assert not mixin._opinions_conflict("Yes, proceed", "Yes, proceed")


@pytest.mark.fast
def test_opinions_conflict_detects_different_approaches() -> None:
    mixin = DummyConsensus()
    assert mixin._opinions_conflict("Use approachA", "Use approachB")
