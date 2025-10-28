"""Role assignment strategies for :class:`~devsynth.domain.models.wsde_core.WSDETeam`.

The historic implementation mutated ``WSDETeam`` in place and relied heavily on
``Any`` typed dictionaries.  That made the code brittle and complicated static
analysis.  This module now exposes a ``RoleAssignmentManager`` that provides a
typed façade around the mutable team state.  Helper functions exported at the
bottom maintain the public API expected by ``wsde_facade`` and tests while
delegating the heavy lifting to the manager.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from collections.abc import Iterable, Mapping, MutableMapping, Sequence

from devsynth.domain.models.wsde_core import WSDETeam
from devsynth.domain.models.wsde_typing import (
    RoleAssignments,
    RoleName,
    SupportsTeamAgent,
    TaskDict,
)
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase

logger = DevSynthLogger(__name__)


ROLE_KEYWORDS: dict[RoleName, tuple[str, ...]] = {
    RoleName.PRIMUS: (
        "leadership",
        "coordination",
        "decision-making",
        "strategic thinking",
    ),
    RoleName.WORKER: ("implementation", "coding", "development", "execution"),
    RoleName.SUPERVISOR: ("oversight", "quality control", "review", "monitoring"),
    RoleName.DESIGNER: ("design", "architecture", "planning", "creativity"),
    RoleName.EVALUATOR: ("testing", "evaluation", "assessment", "analysis"),
}


@dataclass(frozen=True, slots=True)
class ResearchPersonaSpec:
    """Description of a research persona mapped to WSDE responsibilities."""

    slug: str
    display_name: str
    primary_role: RoleName
    supporting_roles: tuple[RoleName, ...]
    capabilities: tuple[str, ...]
    prompt_template: str = ""
    fallback_behavior: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()

    def as_payload(self) -> dict[str, object]:
        """Expose a serialisable payload for telemetry helpers."""

        payload: dict[str, object] = {
            "name": self.display_name,
            "slug": self.slug,
            "primary_role": self.primary_role.value,
            "supporting_roles": [role.value for role in self.supporting_roles],
            "capabilities": list(self.capabilities),
        }
        if self.prompt_template:
            payload["prompt_template"] = self.prompt_template
        if self.fallback_behavior:
            payload["fallback_behavior"] = list(self.fallback_behavior)
        if self.success_criteria:
            payload["success_criteria"] = list(self.success_criteria)
        return payload


def _persona_slug(name: str) -> str:
    return "_".join(part for part in name.strip().lower().split())


def _load_persona_prompt_dataset() -> dict[str, dict[str, object]]:
    """Load persona prompt metadata from the repository template directory."""

    root = Path(__file__).resolve().parents[4]
    dataset_path = root / "templates" / "prompts" / "autoresearch_personas.json"
    if not dataset_path.exists():
        return {}

    with dataset_path.open(encoding="utf-8") as handle:
        content = json.load(handle) or {}

    personas: Mapping[str, dict[str, object]] = content.get("personas", {})
    normalised: dict[str, dict[str, object]] = {}
    for key, value in personas.items():
        slug = _persona_slug(value.get("display_name", key))
        normalised[slug] = value
    return normalised


def _coerce_text_sequence(value: object) -> tuple[str, ...]:
    """Convert ``value`` into a tuple of strings."""

    if not value:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _build_research_persona_specs() -> tuple[ResearchPersonaSpec, ...]:
    """Construct persona specifications enriched with prompt metadata."""

    prompt_dataset = _load_persona_prompt_dataset()

    base_specs = (
        {
            "slug": "research_lead",
            "display_name": "Research Lead",
            "primary_role": RoleName.PRIMUS,
            "supporting_roles": (RoleName.SUPERVISOR,),
            "capabilities": (
                "Coordinate primus leadership for investigative work",
                "Audit research deliverables via supervisor oversight",
                "Plan exploration strategies aligned with task context",
            ),
        },
        {
            "slug": "bibliographer",
            "display_name": "Bibliographer",
            "primary_role": RoleName.EVALUATOR,
            "supporting_roles": (RoleName.WORKER,),
            "capabilities": (
                "Catalogue and vet sources using evaluator analysis",
                "Ground implementation tasks with curated evidence",
                "Flag citation gaps for supervisor review loops",
            ),
        },
        {
            "slug": "synthesist",
            "display_name": "Synthesist",
            "primary_role": RoleName.DESIGNER,
            "supporting_roles": (RoleName.EVALUATOR,),
            "capabilities": (
                "Translate findings into designer implementation plans",
                "Validate analytical coherence before execution",
                "Surface integration risks for primus coordination",
            ),
        },
        {
            "slug": "synthesizer",
            "display_name": "Synthesizer",
            "primary_role": RoleName.WORKER,
            "supporting_roles": (RoleName.DESIGNER, RoleName.EVALUATOR),
            "capabilities": (
                "Convert research packets into worker-ready prototypes with designer foresight",
                "Preserve evaluator traceability tying design choices to cited evidence",
                "Coordinate fallback hand-offs with planner and moderator overlays",
            ),
        },
        {
            "slug": "contrarian",
            "display_name": "Contrarian",
            "primary_role": RoleName.EVALUATOR,
            "supporting_roles": (RoleName.SUPERVISOR,),
            "capabilities": (
                "Challenge consensus through evaluator stress-tests of key assumptions",
                "Document governance-ready dissent logs for supervisor review",
                "Surface risk mitigations before primus decisions are finalised",
            ),
        },
        {
            "slug": "fact_checker",
            "display_name": "Fact Checker",
            "primary_role": RoleName.SUPERVISOR,
            "supporting_roles": (RoleName.EVALUATOR,),
            "capabilities": (
                "Audit claims for supervisor-grade compliance and attribution",
                "Reconstruct evaluator validation chains for contested evidence",
                "Enforce corrective actions before implementation proceeds",
            ),
        },
        {
            "slug": "planner",
            "display_name": "Planner",
            "primary_role": RoleName.DESIGNER,
            "supporting_roles": (RoleName.PRIMUS,),
            "capabilities": (
                "Sequence designer roadmaps that respect primus governance gates",
                "Balance scope, risk, and capacity across supporting roles",
                "Publish contingency playbooks for research-driven pivots",
            ),
        },
        {
            "slug": "moderator",
            "display_name": "Moderator",
            "primary_role": RoleName.PRIMUS,
            "supporting_roles": (RoleName.SUPERVISOR,),
            "capabilities": (
                "Facilitate primus-level decision forums with supervisor safeguards",
                "Resolve persona conflicts while maintaining audit trails",
                "Escalate governance checkpoints when collaboration stalls",
            ),
        },
    )

    specs: list[ResearchPersonaSpec] = []
    for entry in base_specs:
        metadata = prompt_dataset.get(entry["slug"], {})
        prompt_template = str(metadata.get("prompt_template", ""))
        fallback = _coerce_text_sequence(metadata.get("fallback_behavior"))
        success = _coerce_text_sequence(metadata.get("success_criteria"))

        specs.append(
            ResearchPersonaSpec(
                slug=entry["slug"],
                display_name=entry["display_name"],
                primary_role=entry["primary_role"],
                supporting_roles=entry["supporting_roles"],
                capabilities=entry["capabilities"],
                prompt_template=prompt_template,
                fallback_behavior=fallback,
                success_criteria=success,
            )
        )

    return tuple(specs)


RESEARCH_PERSONAS: dict[str, ResearchPersonaSpec] = {
    spec.slug: spec for spec in _build_research_persona_specs()
}


def resolve_research_persona(name: str) -> ResearchPersonaSpec | None:
    """Return the persona specification for ``name`` if it exists."""

    if not name:
        return None
    slug = _persona_slug(name)
    return RESEARCH_PERSONAS.get(slug)


def enumerate_research_personas() -> Sequence[ResearchPersonaSpec]:
    """Return all registered research persona specifications."""

    return tuple(RESEARCH_PERSONAS.values())


def score_agent_for_persona(
    agent: SupportsTeamAgent,
    persona: ResearchPersonaSpec,
    task: TaskDict,
) -> int:
    """Calculate how well ``agent`` aligns with ``persona`` for ``task``."""

    expertise = getattr(agent, "expertise", None) or []
    if not expertise:
        return 0

    task_keywords = _extract_task_keywords(task)
    role_keywords = list(ROLE_KEYWORDS.get(persona.primary_role, ()))
    for role in persona.supporting_roles:
        role_keywords.extend(ROLE_KEYWORDS.get(role, ()))

    score = 0
    for entry in expertise:
        lower_entry = entry.lower()
        for keyword in role_keywords:
            if keyword in lower_entry:
                weight = (
                    2 if keyword in ROLE_KEYWORDS.get(persona.primary_role, ()) else 1
                )
                score += weight
        for keyword in task_keywords:
            if keyword in lower_entry or lower_entry in keyword:
                score += 1
    return score


def select_agent_for_persona(
    agents: Sequence[SupportsTeamAgent],
    persona: ResearchPersonaSpec,
    task: TaskDict,
) -> SupportsTeamAgent | None:
    """Select the most suitable agent for ``persona`` given ``task``."""

    scored = [
        (score_agent_for_persona(agent, persona, task), agent) for agent in agents
    ]
    scored = [item for item in scored if item[0] > 0]
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def persona_event(
    persona: ResearchPersonaSpec,
    agent: SupportsTeamAgent,
    task: TaskDict,
    *,
    fallback: bool,
) -> dict[str, object]:
    """Create a telemetry event for persona assignment."""

    return {
        "persona": persona.display_name,
        "agent": getattr(agent, "name", "agent"),
        "task_id": task.get("id"),
        "phase": str(task.get("phase", "")) or None,
        "fallback": fallback,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _ensure_role_attributes(agent: SupportsTeamAgent) -> None:
    """Initialise bookkeeping attributes on ``agent`` if they are missing."""

    if not hasattr(agent, "has_been_primus"):
        setattr(agent, "has_been_primus", False)
    if not hasattr(agent, "current_role"):
        setattr(agent, "current_role", None)
    if not hasattr(agent, "previous_role"):
        setattr(agent, "previous_role", None)


def _update_agent_role(agent: SupportsTeamAgent, role: RoleName) -> None:
    """Synchronise bookkeeping fields on ``agent`` to reflect ``role``."""

    agent.previous_role = getattr(agent, "current_role", None)
    agent.current_role = role.value.capitalize()
    if role is RoleName.PRIMUS:
        agent.has_been_primus = True


def _normalise_mapping(
    mapping: Mapping[str | RoleName, SupportsTeamAgent | None],
) -> dict[RoleName, SupportsTeamAgent | None]:
    """Convert an arbitrary mapping into a ``RoleName`` keyed dictionary."""

    normalised: dict[RoleName, SupportsTeamAgent | None] = {}
    for key, agent in mapping.items():
        role = key if isinstance(key, RoleName) else RoleName(key)
        normalised[role] = agent
    return normalised


def _agent_name(agent: SupportsTeamAgent | None) -> str | None:
    return None if agent is None else agent.name


@dataclass(slots=True)
class RoleAssignmentManager:
    """Typed façade providing role assignment behaviour."""

    team: WSDETeam

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def assign(
        self, mapping: Mapping[str | RoleName, SupportsTeamAgent] | None = None
    ) -> RoleAssignments:
        """Assign roles either from an explicit mapping or via auto-assignment."""

        self._reset_roles()
        if mapping:
            normalised = _normalise_mapping(mapping)
            self._validate_role_mapping(normalised)
            for role, agent in normalised.items():
                if agent is None:
                    continue
                self.team.roles[role] = agent
                _update_agent_role(agent, role)
        else:
            self._auto_assign_roles()

        logger.info(
            "Role assignments for team %s: %s",
            self.team.name,
            {role.value: _agent_name(agent) for role, agent in self.team.roles.items()},
        )
        return self.team.roles

    def assign_for_phase(self, phase: Phase, task: TaskDict) -> RoleAssignments:
        """Assign roles tailored to a specific EDRR phase."""

        logger.info(
            "Assigning roles for phase %s in team %s", phase.name, self.team.name
        )
        return self._assign_roles_for_phase(phase, task)

    def rotate(self) -> RoleAssignments:
        """Rotate all roles amongst team members."""

        if len(self.team.agents) < 2:
            logger.warning("Cannot rotate roles: need at least 2 agents")
            return self.team.roles

        if not any(agent for _, agent in self.team.roles.items()):
            self._auto_assign_roles()
            return self.team.roles

        ordered_agents: list[SupportsTeamAgent] = [
            agent
            for role in RoleName.ordered()
            if (agent := self.team.roles[role]) is not None
        ]
        unassigned = [
            agent for agent in self.team.agents if agent not in ordered_agents
        ]
        ordered_agents.extend(unassigned)
        if not ordered_agents:
            return self.team.roles

        rotated = ordered_agents[-1:] + ordered_agents[:-1]
        self._reset_roles(clear_agent_history=False)
        for role, agent in zip(RoleName.ordered(), rotated, strict=False):
            self.team.roles[role] = agent
            if agent is not None:
                _update_agent_role(agent, role)

        logger.info(
            "Rotated roles for team %s: %s",
            self.team.name,
            {role.value: _agent_name(agent) for role, agent in self.team.roles.items()},
        )
        return self.team.roles

    def select_primus_by_expertise(self, task: TaskDict) -> SupportsTeamAgent | None:
        if not self.team.agents:
            logger.warning("Cannot select primus: no agents in team")
            return None

        expertise_scores = {
            getattr(agent, "name", str(id(agent))): self._calculate_expertise_score(
                agent, task
            )
            for agent in self.team.agents
        }
        unused_agents = [
            agent
            for agent in self.team.agents
            if not getattr(agent, "has_been_primus", False)
        ]
        if not unused_agents:
            for agent in self.team.agents:
                agent.has_been_primus = False
            unused_agents = list(self.team.agents)

        current_primus = self.team.roles.get(RoleName.PRIMUS)
        if current_primus and current_primus not in unused_agents:
            unused_agents.append(current_primus)

        best_agent = max(
            unused_agents,
            key=lambda agent: expertise_scores.get(
                getattr(agent, "name", str(id(agent))), 0
            ),
        )
        self.team.roles[RoleName.PRIMUS] = best_agent
        _update_agent_role(best_agent, RoleName.PRIMUS)
        self.team.primus_index = self.team.agents.index(best_agent)
        logger.info("Selected %s as primus based on expertise", best_agent.name)
        return best_agent

    def get_role_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for role, agent in self.team.roles.items():
            if agent is not None:
                mapping[agent.name] = role.value.capitalize()
        return mapping

    def get_role_assignments(self) -> dict[str, str]:
        assignments: dict[str, str] = {}
        for role, agent in self.team.roles.items():
            if agent is None:
                continue
            identifier = getattr(agent, "id", agent.name)
            assignments[str(identifier)] = role.value.capitalize()
        return assignments

    def dynamic_reassignment(self, task: TaskDict) -> RoleAssignments:
        primus = self.select_primus_by_expertise(task)
        if primus is not None and primus in self.team.agents:
            self.team.primus_index = self.team.agents.index(primus)
            primus.has_been_primus = True

        phase_value = task.get("phase", Phase.EXPAND)
        phase = (
            phase_value if isinstance(phase_value, Phase) else Phase(str(phase_value))
        )
        return self._assign_roles_for_phase(phase, task)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _reset_roles(self, *, clear_agent_history: bool = True) -> None:
        for agent in self.team.agents:
            _ensure_role_attributes(agent)
            if clear_agent_history:
                agent.previous_role = getattr(agent, "current_role", None)
                agent.current_role = None
        for role in RoleName:
            self.team.roles[role] = None

    def _validate_role_mapping(
        self, mapping: Mapping[RoleName, SupportsTeamAgent | None]
    ) -> None:
        valid_roles = set(RoleName)
        for role, agent in mapping.items():
            if role not in valid_roles:
                raise ValueError(
                    f"Invalid role: {role}. Valid roles are: {', '.join(r.value for r in valid_roles)}"
                )
            if agent is not None and agent not in self.team.agents:
                raise ValueError(f"Agent {agent.name} is not a member of this team")

    def _assign_roles_for_phase(self, phase: Phase, task: TaskDict) -> RoleAssignments:
        self._reset_roles()
        if not self.team.agents:
            logger.warning(
                "Cannot assign roles for phase %s: no agents in team", phase.name
            )
            return self.team.roles

        primus = self.select_primus_by_expertise(task) or self.team.agents[0]
        remaining = [agent for agent in self.team.agents if agent is not primus]
        for role, agent in zip(RoleName.ordered()[1:], remaining, strict=False):
            self.team.roles[role] = agent
            if agent is not None:
                _update_agent_role(agent, role)
        return self.team.roles

    def _auto_assign_roles(self) -> None:
        if not self.team.agents:
            logger.warning("Cannot auto-assign roles: no agents in team")
            return

        self._reset_roles()
        expertise_profiles = {
            getattr(agent, "name", str(id(agent))): self._expertise_profile(agent)
            for agent in self.team.agents
        }
        assigned: set[str] = set()

        primus_candidates = sorted(
            self.team.agents,
            key=lambda agent: expertise_profiles[
                getattr(agent, "name", str(id(agent)))
            ][RoleName.PRIMUS],
            reverse=True,
        )
        if primus_candidates:
            primus = primus_candidates[0]
            self.team.roles[RoleName.PRIMUS] = primus
            _update_agent_role(primus, RoleName.PRIMUS)
            assigned.add(getattr(primus, "name", str(id(primus))))

        for role in RoleName.ordered()[1:]:
            candidates = sorted(
                (
                    agent
                    for agent in self.team.agents
                    if getattr(agent, "name", str(id(agent))) not in assigned
                ),
                key=lambda agent: expertise_profiles[
                    getattr(agent, "name", str(id(agent)))
                ][role],
                reverse=True,
            )
            if not candidates:
                continue
            chosen = candidates[0]
            self.team.roles[role] = chosen
            _update_agent_role(chosen, role)
            assigned.add(getattr(chosen, "name", str(id(chosen))))

    def _expertise_profile(self, agent: SupportsTeamAgent) -> dict[RoleName, int]:
        expertise = getattr(agent, "expertise", None) or []
        profile: dict[RoleName, int] = {}
        for role, keywords in ROLE_KEYWORDS.items():
            profile[role] = sum(
                1
                for keyword in keywords
                for item in expertise
                if keyword.lower() in item.lower()
            )
        return profile

    def _calculate_expertise_score(
        self, agent: SupportsTeamAgent, task: TaskDict
    ) -> int:
        expertise = getattr(agent, "expertise", None) or []
        if not expertise:
            return 0
        keywords = _extract_task_keywords(task)
        score = 0
        for item in expertise:
            lower_item = item.lower()
            score += sum(
                1
                for keyword in keywords
                if keyword in lower_item or lower_item in keyword
            )
        return score

    def _calculate_phase_expertise(
        self, agent: SupportsTeamAgent, task: TaskDict, phase_keywords: Sequence[str]
    ) -> int:
        base = self._calculate_expertise_score(agent, task)
        expertise = getattr(agent, "expertise", None) or []
        phase_score = 0
        for item in expertise:
            lower_item = item.lower()
            phase_score += sum(
                1
                for keyword in phase_keywords
                if keyword in lower_item or lower_item in keyword
            )
        return base + (phase_score * 2)


def _extract_task_keywords(task: TaskDict) -> list[str]:
    keywords: list[str] = []
    description = task.get("description")
    if isinstance(description, str):
        keywords.extend(description.lower().split())
    requirements = task.get("requirements")
    if isinstance(requirements, str):
        keywords.extend(requirements.lower().split())
    elif isinstance(requirements, Iterable):
        for item in requirements:
            if isinstance(item, str):
                keywords.extend(item.lower().split())
            elif isinstance(item, Mapping):
                desc = item.get("description")
                if isinstance(desc, str):
                    keywords.extend(desc.lower().split())
    return keywords


# ---------------------------------------------------------------------------
# Backwards compatible functional façade
# ---------------------------------------------------------------------------


def _manager(team: WSDETeam) -> RoleAssignmentManager:
    manager = getattr(team, "_role_manager", None)
    if not isinstance(manager, RoleAssignmentManager):
        manager = RoleAssignmentManager(team)
        setattr(team, "_role_manager", manager)
    return manager


def assign_roles(
    self: WSDETeam,
    role_mapping: Mapping[str | RoleName, SupportsTeamAgent] | None = None,
) -> RoleAssignments:
    return _manager(self).assign(role_mapping)


def assign_roles_for_phase(
    self: WSDETeam, phase: Phase, task: TaskDict
) -> RoleAssignments:
    return _manager(self).assign_for_phase(phase, task)


def dynamic_role_reassignment(self: WSDETeam, task: TaskDict) -> RoleAssignments:
    return _manager(self).dynamic_reassignment(task)


def _validate_role_mapping(
    self: WSDETeam, mapping: Mapping[str | RoleName, SupportsTeamAgent | None]
) -> None:
    _manager(self)._validate_role_mapping(_normalise_mapping(mapping))


def _auto_assign_roles(self: WSDETeam) -> None:
    _manager(self)._auto_assign_roles()


def get_role_map(self: WSDETeam) -> dict[str, str]:
    return _manager(self).get_role_map()


def get_role_assignments(self: WSDETeam) -> dict[str, str]:
    return _manager(self).get_role_assignments()


def _calculate_expertise_score(
    self: WSDETeam, agent: SupportsTeamAgent, task: TaskDict
) -> int:
    return _manager(self)._calculate_expertise_score(agent, task)


def _calculate_phase_expertise_score(
    self: WSDETeam,
    agent: SupportsTeamAgent,
    task: TaskDict,
    phase_keywords: Sequence[str],
) -> int:
    return _manager(self)._calculate_phase_expertise(agent, task, phase_keywords)


def select_primus_by_expertise(
    self: WSDETeam, task: TaskDict
) -> SupportsTeamAgent | None:
    return _manager(self).select_primus_by_expertise(task)


def rotate_roles(self: WSDETeam) -> RoleAssignments:
    return _manager(self).rotate()


def _assign_roles_for_edrr_phase(
    self: WSDETeam, phase: Phase, task: TaskDict
) -> RoleAssignments:
    return _manager(self)._assign_roles_for_phase(phase, task)


__all__ = [
    "assign_roles",
    "assign_roles_for_phase",
    "dynamic_role_reassignment",
    "_validate_role_mapping",
    "_auto_assign_roles",
    "get_role_map",
    "get_role_assignments",
    "_calculate_expertise_score",
    "_calculate_phase_expertise_score",
    "select_primus_by_expertise",
    "rotate_roles",
    "_assign_roles_for_edrr_phase",
    "ResearchPersonaSpec",
    "RESEARCH_PERSONAS",
    "resolve_research_persona",
    "enumerate_research_personas",
    "score_agent_for_persona",
    "select_agent_for_persona",
    "persona_event",
]
