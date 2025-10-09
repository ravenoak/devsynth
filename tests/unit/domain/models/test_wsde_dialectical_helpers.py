"""Focused tests for WSDE dialectical helper functions."""

import pytest

from devsynth.domain.models import wsde_dialectical
from devsynth.domain.models.wsde_dialectical import (
    AntithesisDraft,
    Critique,
    ResolutionPlan,
)
from devsynth.domain.models.wsde_facade import WSDETeam


class DummyCritic:
    """Lightweight critic stub exposing a name attribute."""

    def __init__(self, name: str = "critic") -> None:
        self.name = name


@pytest.mark.fast
def test_generate_antithesis_returns_typed_draft() -> None:
    team = WSDETeam(name="dialectical-test")
    thesis = {"content": "Short text without example.", "code": "print('hi')"}
    draft = wsde_dialectical._generate_antithesis(team, thesis, DummyCritic())

    assert isinstance(draft, AntithesisDraft)
    assert draft.critic_id == "critic"
    assert draft.critiques  # populated from content/code heuristics
    assert any("brief" in message.lower() for message in draft.critiques)
    assert draft.improvement_suggestions
    assert draft.alternative_approaches


@pytest.mark.fast
def test_categorize_critiques_by_domain_returns_tuples() -> None:
    team = WSDETeam(name="categorise-test")
    critiques = [
        "Security issue: Missing authentication checks",
        "Documentation content does not include examples",
    ]

    mapping = team._categorize_critiques_by_domain(critiques)

    assert mapping == {
        "security": ("Security issue: Missing authentication checks",),
        "content": ("Documentation content does not include examples",),
    }


@pytest.mark.fast
def test_generate_synthesis_returns_resolution_plan() -> None:
    team = WSDETeam(name="synthesis-test")
    thesis = {
        "content": "Short text without example.",
        "code": "print('hello')",
    }
    draft = wsde_dialectical._generate_antithesis(team, thesis, DummyCritic())
    domain_map = team._categorize_critiques_by_domain(draft.critiques)
    message_domains = wsde_dialectical._invert_domain_mapping(domain_map)

    critiques = [
        Critique.from_message(
            reviewer_id=draft.critic_id,
            ordinal=index,
            message=message,
            domains=message_domains.get(message, ()),
            metadata={"antithesis_id": draft.identifier},
        )
        for index, message in enumerate(draft.critiques)
    ]

    plan = wsde_dialectical._generate_synthesis(
        team,
        thesis,
        draft,
        tuple(critiques),
        domain_map,
    )

    assert isinstance(plan, ResolutionPlan)
    assert all(isinstance(item, Critique) for item in plan.integrated_critiques)
    assert isinstance(plan.improvements, tuple)
    assert plan.standards_compliance
    # Ensure rejected critiques refer back to the critic when falling back
    for critique in plan.rejected_critiques:
        assert isinstance(critique, Critique)
        assert critique.reviewer_id == draft.critic_id
