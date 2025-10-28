"""Shared fixtures for WSDE domain model unit tests."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable
from uuid import uuid4

import pytest

from devsynth.domain.models import (
    wsde_code_improvements,
    wsde_decision_making,
    wsde_enhanced_dialectical,
    wsde_security_checks,
    wsde_solution_analysis,
)
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

    def generate_ideas(
        self, task: dict[str, Any], max_ideas: int = 3
    ) -> list[dict[str, Any]]:
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
        return _bind_module_helpers(team)

    return _factory


@pytest.fixture
def wsde_module_team(
    wsde_team_factory: Callable[..., WSDETeam],
    stub_agent_factory: Callable[..., StubWSDEAgent],
) -> tuple[WSDETeam, dict[str, StubWSDEAgent]]:
    """Provision a WSDE team preloaded with versatile stub agents for module tests."""

    innovator = stub_agent_factory(
        "innovator",
        expertise=["security", "performance", "generalist"],
        idea_batches=[
            [
                {
                    "id": "idea-secure-cache",
                    "description": "Add secure caching layer",
                    "rationale": "Protect data in-flight while reducing latency",
                },
                {
                    "id": "idea-audit",
                    "description": "Introduce continuous auditing",
                    "rationale": "Ensure regulatory alignment",
                },
            ],
            [
                {
                    "id": "idea-batch",
                    "description": "Batch telemetry uploads",
                    "rationale": "Improve throughput for monitoring",
                }
            ],
        ],
        evaluation_scores={
            "feasibility": {
                "idea-secure-cache": 0.8,
                "idea-audit": 0.4,
                "idea-batch": 0.7,
            },
            "impact": {
                "idea-secure-cache": 0.9,
                "idea-audit": 0.5,
                "idea-batch": 0.6,
            },
        },
    )

    critic = stub_agent_factory(
        "critic",
        expertise=["security", "analysis"],
        critique_response={
            "critiques": [
                "Encryption is missing from the data store",
                "Performance profile lacks stress data",
            ],
            "improvement_suggestions": [
                "Adopt envelope encryption",
                "Document load testing assumptions",
            ],
            "domain_specific_feedback": {
                "security": ["Encryption missing"],
                "performance": ["No stress benchmarks"],
                "code_quality": ["Functions exceed 80 lines"],
            },
        },
    )

    reviewer = stub_agent_factory(
        "reviewer",
        expertise=["review", "knowledge"],
        idea_batches=[
            [
                {
                    "id": "idea-secure-cache",
                    "description": "Add secure caching layer",
                    "rationale": "Protect data in-flight while reducing latency",
                }
            ]
        ],
        evaluation_scores={
            "feasibility": {
                "idea-secure-cache": 0.7,
                "idea-audit": 0.6,
                "idea-batch": 0.8,
            },
            "impact": {
                "idea-secure-cache": 0.85,
                "idea-audit": 0.55,
                "idea-batch": 0.65,
            },
        },
        critique_response={
            "critiques": [
                "Knowledge base lacks lessons learned",
            ],
            "improvement_suggestions": [
                "Integrate retrospective summaries",
            ],
            "domain_specific_feedback": {
                "knowledge_management": [
                    "Summaries do not mention compliance incidents"
                ]
            },
        },
    )

    redundant = stub_agent_factory(
        "redundant",
        expertise=["operations"],
        idea_batches=[
            [
                {
                    "id": "idea-secure-cache",
                    "description": "Add secure caching layer",
                    "rationale": "Protect data in-flight while reducing latency",
                }
            ]
        ],
    )

    team = wsde_team_factory(
        name="wsde-module-team",
        description="Stubbed WSDE team for module integration tests",
        agents=[innovator, critic, reviewer, redundant],
    )
    _bind_module_helpers(team)

    return team, {
        "innovator": innovator,
        "critic": critic,
        "reviewer": reviewer,
        "redundant": redundant,
    }


def _bind_module_helpers(team: WSDETeam) -> WSDETeam:
    """Attach module helper functions to the WSDETeam instance when absent."""

    method_bindings: dict[str, Any] = {
        "_improve_credentials": wsde_code_improvements._improve_credentials,
        "_improve_error_handling": wsde_code_improvements._improve_error_handling,
        "_improve_input_validation": wsde_code_improvements._improve_input_validation,
        "_improve_security": wsde_code_improvements._improve_security,
        "_calculate_idea_similarity": wsde_decision_making._calculate_idea_similarity,
        "_analyze_solution": wsde_solution_analysis._analyze_solution,
        "_generate_comparative_analysis": wsde_solution_analysis._generate_comparative_analysis,
        "_check_security_best_practices": wsde_security_checks._check_security_best_practices,
        "_balance_security_and_performance": wsde_security_checks._balance_security_and_performance,
        "_balance_security_and_usability": wsde_security_checks._balance_security_and_usability,
        "_balance_performance_and_maintainability": wsde_security_checks._balance_performance_and_maintainability,
    }

    for attribute, function in method_bindings.items():
        if not hasattr(team, attribute):
            setattr(team, attribute, function.__get__(team, WSDETeam))

    def _detailed_synthesis_reasoning(
        self: WSDETeam,
        domain_critiques: Any,
        domain_improvements: Any,
        domain_conflicts: Any,
        resolved_conflicts: Any,
        standards_compliance: Any,
    ) -> str:
        return wsde_enhanced_dialectical._generate_detailed_synthesis_reasoning(
            domain_critiques,
            domain_improvements,
            domain_conflicts,
            resolved_conflicts,
            standards_compliance,
        )

    team._generate_detailed_synthesis_reasoning = _detailed_synthesis_reasoning.__get__(
        team, WSDETeam
    )

    return team
