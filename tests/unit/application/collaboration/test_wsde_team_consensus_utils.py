from unittest.mock import MagicMock

from devsynth.application.collaboration.wsde_team_consensus import (
    ConsensusBuildingMixin,
)


class DummyConsensus(ConsensusBuildingMixin):
    def __init__(self):
        self.logger = MagicMock()
        self.agents = []


def test_opinions_conflict_detects_contradictions():
    mixin = DummyConsensus()
    assert mixin._opinions_conflict("Yes, proceed", "No, stop")
    assert not mixin._opinions_conflict("Yes, proceed", "Yes, proceed")


def test_opinions_conflict_detects_different_approaches():
    mixin = DummyConsensus()
    assert mixin._opinions_conflict("Use approachA", "Use approachB")
