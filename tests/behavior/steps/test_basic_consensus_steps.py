"""BDD steps for consensus building.

Issue: issues/consensus-building.md
"""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.consensus import build_consensus
from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast

scenarios(feature_path(__file__, "general", "consensus_building.feature"))


@pytest.fixture
def context():
    """Issue: issues/consensus-building.md"""

    class Context:
        votes: list[str]
        result: Any | None

        def __init__(self) -> None:
            self.votes = []
            self.result = None

    return Context()


@given(parsers.parse('votes "{csv}"'))
def parse_votes(context, csv: str) -> None:
    """Issue: issues/consensus-building.md"""

    context.votes = [v.strip() for v in csv.split(",") if v]


@when("we build consensus")
def build_default(context) -> None:
    """Issue: issues/consensus-building.md"""

    context.result = build_consensus(context.votes)


@when(parsers.parse("we build consensus with threshold {threshold:f}"))
def build_with_threshold(context, threshold: float) -> None:
    """Issue: issues/consensus-building.md"""

    context.result = build_consensus(context.votes, threshold=threshold)


@then(parsers.parse('consensus decision is "{expected}"'))
def expect_decision(context, expected: str) -> None:
    """Issue: issues/consensus-building.md"""

    assert context.result.decision == expected
    assert context.result.consensus is True


@then("no consensus decision is made")
def expect_no_decision(context) -> None:
    """Issue: issues/consensus-building.md"""

    assert context.result.consensus is False
    assert context.result.decision is None
