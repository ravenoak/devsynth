"""Shared fixtures for WSDE domain model unit tests."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import uuid4

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam


@dataclass
class StubWSDEAgent:
    """Test double that mimics the narrow WSDE agent interface."""

    name: str
    expertise: Sequence[str] = field(default_factory=tuple)
    idea_batches: list[list[dict[str, Any]]] = field(default_factory=list)
    evaluation_scores: dict[str, dict[str, float]] = field(default_factory=dict)
    critique_response: dict[str, Any] | None = None
    idea_error_factory: Callable[[], Exception] | None = None
    critique_error_factory: Callable[[], Exception] | None = None
    discipline: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def generate_ideas(self, task: dict[str, Any], max_ideas: int = 3) -> list[dict[str, Any]]:
        """Return a predictable batch of ideas or raise a configured error."""

        if self.idea_error_factory is not None:
            raise self.idea_error_factory()

        if not self.idea_batches:
            return []

        batch = self.idea_batches.pop(0)
        ideas: list[dict[str, Any]] = []
        for idea in batch[:max_ideas]:
            clone = dict(idea)
            clone.setdefault("description", "")
            clone.setdefault("rationale", "")
            ideas.append(clone)
        return ideas

    def evaluate_idea(self, idea: dict[str, Any], criterion: str) -> float:
        """Look up the score for ``criterion`` and idea identifier."""

        criterion_scores = self.evaluation_scores.get(criterion, {})
        identifier = idea.get("id") or idea.get("description")
        return float(criterion_scores.get(identifier, 0.0))

    def critique(self, request: dict[str, Any]) -> dict[str, Any]:
        """Return a canned critique or raise an injected error."""

        if self.critique_error_factory is not None:
            raise self.critique_error_factory()
        if self.critique_response is not None:
            return self.critique_response
        return {
            "critiques": ["Default critique"],
            "improvement_suggestions": [],
            "domain_specific_feedback": {},
        }


@pytest.fixture
def stub_agent_factory() -> Callable[..., StubWSDEAgent]:
    """Factory fixture that creates stub WSDE agents for tests."""

    def _factory(
        name: str,
        *,
        expertise: Sequence[str] | None = None,
        idea_batches: Iterable[Iterable[dict[str, Any]]] | None = None,
        evaluation_scores: dict[str, dict[str, float]] | None = None,
        critique_response: dict[str, Any] | None = None,
        idea_error_factory: Callable[[], Exception] | None = None,
        critique_error_factory: Callable[[], Exception] | None = None,
        discipline: str | None = None,
        agent_id: str | None = None,
    ) -> StubWSDEAgent:
        batches = [list(batch) for batch in idea_batches] if idea_batches else []
        return StubWSDEAgent(
            name=name,
            expertise=tuple(expertise or ()),
            idea_batches=batches,
            evaluation_scores=evaluation_scores or {},
            critique_response=critique_response,
            idea_error_factory=idea_error_factory,
            critique_error_factory=critique_error_factory,
            discipline=discipline,
            id=agent_id or str(uuid4()),
        )

    return _factory


@pytest.fixture
def wsde_team_factory() -> Callable[..., WSDETeam]:
    """Factory fixture that constructs WSDE teams with stub agents."""

    def _factory(
        *,
        name: str = "wsde-test-team",
        description: str | None = None,
        agents: Iterable[StubWSDEAgent] | None = None,
    ) -> WSDETeam:
        team = WSDETeam(name=name, description=description, agents=list(agents or ()))
        return team

    return _factory
