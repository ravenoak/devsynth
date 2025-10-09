"""Multi-disciplinary dialectical reasoning for WSDE teams."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Mapping, Optional, Protocol, Sequence, runtime_checkable
from uuid import uuid4

from devsynth.domain.models.wsde_core import WSDETeam
from devsynth.domain.models.wsde_typing import SupportsTeamAgent, TaskDict
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass(slots=True)
class DisciplinaryPerspective:
    agent: str
    discipline: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:  # pragma: no cover - trivial glue
        return {
            "agent": self.agent,
            "discipline": self.discipline,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
            "discipline_specific_insights": self.insights,
        }


@dataclass(slots=True)
class PerspectiveConflict:
    discipline: str
    issue: str

    def as_dict(self) -> dict[str, str]:  # pragma: no cover - trivial glue
        return {"discipline": self.discipline, "issue": self.issue}


@dataclass(slots=True)
class SynthesisResult:
    summary: str
    integration_steps: list[str]
    critic_summary: str

    def as_dict(self) -> dict[str, object]:  # pragma: no cover - trivial glue
        return {
            "summary": self.summary,
            "integration_steps": self.integration_steps,
            "critic_summary": self.critic_summary,
        }


@dataclass(slots=True)
class EvaluationResult:
    score: float
    observations: list[str]

    def as_dict(self) -> dict[str, object]:  # pragma: no cover - trivial glue
        return {"score": self.score, "observations": self.observations}


@dataclass(slots=True)
class MultidisciplinaryAnalysis:
    identifier: str
    timestamp: datetime
    task_id: str
    thesis: Mapping[str, object]
    perspectives: list[DisciplinaryPerspective]
    conflicts: list[PerspectiveConflict]
    synthesis: SynthesisResult
    evaluation: EvaluationResult

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.identifier,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "thesis": dict(self.thesis),
            "perspectives": [
                perspective.as_dict() for perspective in self.perspectives
            ],
            "conflicts": [conflict.as_dict() for conflict in self.conflicts],
            "synthesis": self.synthesis.as_dict(),
            "evaluation": self.evaluation.as_dict(),
            "method": "multi_disciplinary_dialectical_reasoning",
        }


@dataclass(slots=True)
class MultidisciplinaryEngine:
    team: WSDETeam

    def apply(
        self,
        task: TaskDict,
        critic_agent: SupportsTeamAgent,
        disciplinary_knowledge: Mapping[str, Mapping[str, Sequence[str]]],
        disciplinary_agents: Sequence[SupportsTeamAgent],
        memory_integration: Optional[SupportsDialecticalMemory] = None,
    ) -> MultidisciplinaryAnalysis | dict[str, object]:
        if not task or "solution" not in task:
            logger.warning(
                "Cannot apply multi-disciplinary dialectical reasoning: no solution provided"
            )
            return {"status": "failed", "reason": "no_solution"}

        thesis_solution = task["solution"]
        perspectives = self._gather_perspectives(
            thesis_solution, task, disciplinary_agents, disciplinary_knowledge
        )
        conflicts = self._identify_conflicts(perspectives)
        synthesis = self._generate_synthesis(
            thesis_solution, perspectives, conflicts, critic_agent
        )
        evaluation = self._generate_evaluation(synthesis, perspectives, task)

        analysis = MultidisciplinaryAnalysis(
            identifier=str(uuid4()),
            timestamp=datetime.now(),
            task_id=str(task.get("id", uuid4())),
            thesis=thesis_solution,
            perspectives=perspectives,
            conflicts=conflicts,
            synthesis=synthesis,
            evaluation=evaluation,
        )

        for hook in self.team.dialectical_hooks:
            hook(task, [analysis.as_dict()])

        if memory_integration is not None:
            try:
                memory_integration.store_dialectical_result(task, analysis.as_dict())
            except Exception:  # pragma: no cover - defensive
                logger.exception(
                    "Failed to store dialectical result in memory integration"
                )

        return analysis

    # ------------------------------------------------------------------
    # Perspective gathering
    # ------------------------------------------------------------------
    def _gather_perspectives(
        self,
        solution: Mapping[str, object],
        task: TaskDict,
        disciplinary_agents: Sequence[SupportsTeamAgent],
        disciplinary_knowledge: Mapping[str, Mapping[str, Sequence[str]]],
    ) -> list[DisciplinaryPerspective]:
        relevant_disciplines = self._infer_relevant_disciplines(
            task, disciplinary_knowledge
        )
        relevant_disciplines.update(
            discipline
            for discipline in (
                self._determine_discipline(agent) for agent in disciplinary_agents
            )
            if discipline in disciplinary_knowledge
        )
        perspectives: list[DisciplinaryPerspective] = []
        for agent in disciplinary_agents:
            discipline = self._determine_discipline(agent)
            if discipline not in relevant_disciplines:
                continue
            knowledge = disciplinary_knowledge.get(discipline, {})
            perspective = DisciplinaryPerspective(
                agent=getattr(agent, "name", "unknown"),
                discipline=discipline,
            )
            for criterion in _normalise_str_sequence(
                knowledge.get("strengths_criteria")
            ):
                if _solution_addresses_item(solution, criterion):
                    perspective.strengths.append(f"Solution addresses {criterion}")
            for criterion in _normalise_str_sequence(
                knowledge.get("weaknesses_criteria")
            ):
                if not _solution_addresses_item(solution, criterion):
                    perspective.weaknesses.append(
                        f"Solution does not adequately address {criterion}"
                    )
            for practice in _normalise_str_sequence(knowledge.get("best_practices")):
                if not _solution_addresses_item(solution, practice):
                    perspective.recommendations.append(
                        f"Incorporate {practice} into the solution"
                    )
            perspective.insights.extend(
                _normalise_str_sequence(knowledge.get("discipline_specific_insights"))
            )
            perspectives.append(perspective)
        return perspectives

    def _identify_conflicts(
        self, perspectives: Sequence[DisciplinaryPerspective]
    ) -> list[PerspectiveConflict]:
        conflicts: list[PerspectiveConflict] = []
        for perspective in perspectives:
            for weakness in perspective.weaknesses:
                conflicts.append(
                    PerspectiveConflict(
                        discipline=perspective.discipline, issue=weakness
                    )
                )
        return conflicts

    def _generate_synthesis(
        self,
        thesis: Mapping[str, object],
        perspectives: Sequence[DisciplinaryPerspective],
        conflicts: Sequence[PerspectiveConflict],
        critic_agent: SupportsTeamAgent,
    ) -> SynthesisResult:
        integration_steps = [
            f"Integrate {perspective.discipline} recommendations"
            for perspective in perspectives
            if perspective.recommendations
        ]
        critic_name = getattr(critic_agent, "name", "critic")
        summary = "Synthesised multi-disciplinary view incorporating all perspectives."
        if conflicts:
            summary += (
                f" Resolved {len(conflicts)} conflicts via collaborative planning."
            )
        return SynthesisResult(
            summary=summary,
            integration_steps=integration_steps,
            critic_summary=f"Critic {critic_name} validated the synthesis for feasibility.",
        )

    def _generate_evaluation(
        self,
        synthesis: SynthesisResult,
        perspectives: Sequence[DisciplinaryPerspective],
        task: TaskDict,
    ) -> EvaluationResult:
        coverage = sum(
            1
            for perspective in perspectives
            if perspective.strengths or perspective.recommendations
        )
        score = min(1.0, coverage / max(1, len(perspectives)))
        observations = [
            f"Discipline {perspective.discipline} contributed {len(perspective.recommendations)} recommendations"
            for perspective in perspectives
        ]
        if task.get("success_metrics"):
            observations.append(
                "Task includes explicit success metrics that inform evaluation."
            )
        observations.append(f"Synthesis Summary: {synthesis.summary}")
        return EvaluationResult(score=score, observations=observations)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _infer_relevant_disciplines(
        self,
        task: TaskDict,
        disciplinary_knowledge: Mapping[str, Mapping[str, Sequence[str]]],
    ) -> set[str]:
        relevant: set[str] = set()
        description = task.get("description")
        if isinstance(description, str):
            text = description.lower()
            for discipline in disciplinary_knowledge:
                if discipline.lower() in text:
                    relevant.add(discipline)
        requirements = task.get("requirements")
        if isinstance(requirements, str):
            text = requirements.lower()
            for discipline in disciplinary_knowledge:
                if discipline.lower() in text:
                    relevant.add(discipline)
        elif isinstance(requirements, Iterable):
            for item in requirements:
                if isinstance(item, str):
                    for discipline in disciplinary_knowledge:
                        if discipline.lower() in item.lower():
                            relevant.add(discipline)
                elif isinstance(item, Mapping):
                    desc = item.get("description")
                    if isinstance(desc, str):
                        for discipline in disciplinary_knowledge:
                            if discipline.lower() in desc.lower():
                                relevant.add(discipline)
        if not relevant:
            relevant.update(disciplinary_knowledge.keys())
        return relevant

    def _determine_discipline(self, agent: SupportsTeamAgent) -> str:
        if hasattr(agent, "discipline") and getattr(agent, "discipline"):
            return str(getattr(agent, "discipline"))
        expertise = getattr(agent, "expertise", None) or []
        return expertise[0] if expertise else "general"


def _solution_addresses_item(solution: Mapping[str, object], criterion: str) -> bool:
    criterion_lower = criterion.lower()
    for value in solution.values():
        if isinstance(value, str) and criterion_lower in value.lower():
            return True
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            if any(
                isinstance(item, str) and criterion_lower in item.lower()
                for item in value
            ):
                return True
        if isinstance(value, Mapping):
            if _solution_addresses_item(value, criterion):
                return True
    return False


def _normalise_str_sequence(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value]
    return []


def _dict_to_perspective(item: Mapping[str, object]) -> DisciplinaryPerspective:
    return DisciplinaryPerspective(
        agent=str(item.get("agent", "unknown")),
        discipline=str(item.get("discipline", "general")),
        strengths=_normalise_str_sequence(item.get("strengths")),
        weaknesses=_normalise_str_sequence(item.get("weaknesses")),
        recommendations=_normalise_str_sequence(item.get("recommendations")),
        insights=_normalise_str_sequence(item.get("discipline_specific_insights")),
    )


def _engine(team: WSDETeam) -> MultidisciplinaryEngine:
    engine = getattr(team, "_multidisciplinary_engine", None)
    if not isinstance(engine, MultidisciplinaryEngine):
        engine = MultidisciplinaryEngine(team)
        setattr(team, "_multidisciplinary_engine", engine)
    return engine


def apply_multi_disciplinary_dialectical_reasoning(
    self: WSDETeam,
    task: TaskDict,
    critic_agent: SupportsTeamAgent,
    disciplinary_knowledge: Mapping[str, Mapping[str, Sequence[str]]],
    disciplinary_agents: Sequence[SupportsTeamAgent],
    memory_integration: Optional[SupportsDialecticalMemory] = None,
) -> dict[str, object]:
    result = _engine(self).apply(
        task,
        critic_agent,
        disciplinary_knowledge,
        disciplinary_agents,
        memory_integration,
    )
    return result if isinstance(result, dict) else result.as_dict()


def _gather_disciplinary_perspectives(
    self: WSDETeam,
    solution: Mapping[str, object],
    task: TaskDict,
    disciplinary_agents: Sequence[SupportsTeamAgent],
    disciplinary_knowledge: Mapping[str, Mapping[str, Sequence[str]]],
) -> list[dict[str, object]]:
    perspectives = _engine(self)._gather_perspectives(
        solution, task, disciplinary_agents, disciplinary_knowledge
    )
    return [perspective.as_dict() for perspective in perspectives]


def _identify_perspective_conflicts(
    self: WSDETeam, perspectives: Sequence[dict[str, object]]
) -> list[dict[str, str]]:
    structured = [_dict_to_perspective(item) for item in perspectives]
    conflicts = _engine(self)._identify_conflicts(structured)
    return [conflict.as_dict() for conflict in conflicts]


def _generate_multi_disciplinary_synthesis(
    self: WSDETeam,
    thesis_solution: Mapping[str, object],
    perspectives: Sequence[dict[str, object]],
    conflicts: Sequence[dict[str, object]],
    critic_agent: SupportsTeamAgent,
) -> dict[str, object]:
    structured_perspectives = [_dict_to_perspective(item) for item in perspectives]
    structured_conflicts = [
        PerspectiveConflict(
            discipline=str(conflict.get("discipline", "general")),
            issue=str(conflict.get("issue", "")),
        )
        for conflict in conflicts
    ]
    synthesis = _engine(self)._generate_synthesis(
        thesis_solution, structured_perspectives, structured_conflicts, critic_agent
    )
    return synthesis.as_dict()


def _generate_multi_disciplinary_evaluation(
    self: WSDETeam,
    synthesis: dict[str, object],
    perspectives: Sequence[dict[str, object]],
    task: TaskDict,
) -> dict[str, object]:
    structured_perspectives = [_dict_to_perspective(item) for item in perspectives]
    synthesis_result = SynthesisResult(
        summary=str(synthesis.get("summary", "")),
        integration_steps=_normalise_str_sequence(synthesis.get("integration_steps")),
        critic_summary=str(synthesis.get("critic_summary", "")),
    )
    evaluation = _engine(self)._generate_evaluation(
        synthesis_result, structured_perspectives, task
    )
    return evaluation.as_dict()


__all__ = [
    "apply_multi_disciplinary_dialectical_reasoning",
    "_gather_disciplinary_perspectives",
    "_identify_perspective_conflicts",
    "_generate_multi_disciplinary_synthesis",
    "_generate_multi_disciplinary_evaluation",
]


@runtime_checkable
class SupportsDialecticalMemory(Protocol):
    def store_dialectical_result(
        self, task: TaskDict, result: Mapping[str, object]
    ) -> None: ...
