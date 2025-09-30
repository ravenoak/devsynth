"""Role assignment strategies for :class:`~devsynth.domain.models.wsde_core.WSDETeam`.

The historic implementation mutated ``WSDETeam`` in place and relied heavily on
``Any`` typed dictionaries.  That made the code brittle and complicated static
analysis.  This module now exposes a ``RoleAssignmentManager`` that provides a
typed façade around the mutable team state.  Helper functions exported at the
bottom maintain the public API expected by ``wsde_facade`` and tests while
delegating the heavy lifting to the manager.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, Optional, Sequence

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


@dataclass(frozen=True, slots=True)
class ResearchPersonaDefinition:
    """Description of a research persona mapped to WSDE responsibilities."""

    identifier: str
    title: str
    primary_role: RoleName
    supporting_roles: tuple[RoleName, ...]
    capabilities: tuple[str, ...]
    fallback_role: RoleName

    def keywords(self) -> tuple[str, ...]:  # pragma: no cover - trivial helper
        return self.capabilities


RESEARCH_PERSONA_DEFINITIONS: dict[str, ResearchPersonaDefinition] = {
    "research_lead": ResearchPersonaDefinition(
        identifier="research_lead",
        title="Research Lead",
        primary_role=RoleName.PRIMUS,
        supporting_roles=(RoleName.DESIGNER, RoleName.SUPERVISOR),
        capabilities=(
            "research strategy",
            "query planning",
            "knowledge graph navigation",
            "investigation leadership",
        ),
        fallback_role=RoleName.PRIMUS,
    ),
    "bibliographer": ResearchPersonaDefinition(
        identifier="bibliographer",
        title="Bibliographer",
        primary_role=RoleName.SUPERVISOR,
        supporting_roles=(RoleName.EVALUATOR,),
        capabilities=(
            "source vetting",
            "citation management",
            "evidence curation",
            "literature review",
        ),
        fallback_role=RoleName.SUPERVISOR,
    ),
    "synthesist": ResearchPersonaDefinition(
        identifier="synthesist",
        title="Synthesist",
        primary_role=RoleName.EVALUATOR,
        supporting_roles=(RoleName.DESIGNER, RoleName.WORKER),
        capabilities=(
            "insight synthesis",
            "comparative analysis",
            "recommendation drafting",
            "implementation guidance",
        ),
        fallback_role=RoleName.EVALUATOR,
    ),
}


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


def get_research_persona(identifier: str) -> ResearchPersonaDefinition:
    """Return the research persona definition for ``identifier``."""

    normalised = identifier.lower().strip()
    persona = RESEARCH_PERSONA_DEFINITIONS.get(normalised)
    if persona is None:
        raise KeyError(f"Unknown research persona: {identifier}")
    return persona


def iter_research_personas() -> tuple[ResearchPersonaDefinition, ...]:  # pragma: no cover - simple helper
    return tuple(RESEARCH_PERSONA_DEFINITIONS.values())


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
    mapping: Mapping[str | RoleName, SupportsTeamAgent | None]
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
        self, mapping: Optional[Mapping[str | RoleName, SupportsTeamAgent]] = None
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

        logger.info("Assigning roles for phase %s in team %s", phase.name, self.team.name)
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
            agent for role in RoleName.ordered() if (agent := self.team.roles[role]) is not None
        ]
        unassigned = [agent for agent in self.team.agents if agent not in ordered_agents]
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
            getattr(agent, "name", str(id(agent))): self._calculate_expertise_score(agent, task)
            for agent in self.team.agents
        }
        unused_agents = [agent for agent in self.team.agents if not getattr(agent, "has_been_primus", False)]
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

    def select_primus_for_persona(
        self, task: TaskDict, persona: ResearchPersonaDefinition
    ) -> SupportsTeamAgent | None:
        """Select a primus that best matches the requested research persona."""

        if not self.team.agents:
            logger.warning("Cannot select primus: no agents in team")
            return None

        self._ensure_persona_bookkeeping()
        keywords = {kw.lower() for kw in persona.capabilities}
        if not keywords:
            return self.select_primus_by_expertise(task)

        best_agent: SupportsTeamAgent | None = None
        best_score = -1
        for agent in self.team.agents:
            expertise = getattr(agent, "expertise", None) or []
            lower_expertise = [item.lower() for item in expertise]
            persona_hits = sum(
                1 for keyword in keywords for item in lower_expertise if keyword in item
            )
            base_score = self._calculate_expertise_score(agent, task)
            support_bonus = sum(
                1
                for role in persona.supporting_roles
                if getattr(agent, "current_role", "").lower() == role.value
            )
            total_score = base_score + (persona_hits * 2) + support_bonus
            if total_score > best_score:
                best_agent = agent
                best_score = total_score

        if best_agent is None or best_score <= 0:
            fallback = self.select_primus_by_expertise(task)
            if fallback is not None:
                self._record_persona_event(
                    persona.identifier,
                    fallback,
                    task,
                    fallback_used=True,
                )
            return fallback

        self.team.roles[RoleName.PRIMUS] = best_agent
        _update_agent_role(best_agent, persona.primary_role)
        setattr(best_agent, "active_persona", persona.identifier)
        self.team.primus_index = self.team.agents.index(best_agent)
        self._record_persona_event(persona.identifier, best_agent, task)
        logger.info(
            "Selected %s as primus for persona %s", best_agent.name, persona.identifier
        )
        return best_agent

    # ------------------------------------------------------------------
    # Persona helpers
    # ------------------------------------------------------------------

    def _ensure_persona_bookkeeping(self) -> None:
        if not hasattr(self.team, "research_persona_assignments"):
            setattr(self.team, "research_persona_assignments", {})
        if not hasattr(self.team, "research_persona_telemetry"):
            setattr(self.team, "research_persona_telemetry", [])

    def _record_persona_event(
        self,
        persona_identifier: str,
        agent: SupportsTeamAgent,
        task: TaskDict,
        *,
        fallback_used: bool = False,
    ) -> None:
        self._ensure_persona_bookkeeping()
        assignments: MutableMapping[str, str] = getattr(
            self.team, "research_persona_assignments"
        )
        assignments[persona_identifier] = getattr(agent, "name", "agent")
        telemetry: list[dict[str, object]] = getattr(
            self.team, "research_persona_telemetry"
        )
        telemetry.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "persona": persona_identifier,
                "agent": getattr(agent, "name", "agent"),
                "task_id": str(task.get("id", "unknown")),
                "fallback": fallback_used,
            }
        )

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
        phase = phase_value if isinstance(phase_value, Phase) else Phase(str(phase_value))
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
            logger.warning("Cannot assign roles for phase %s: no agents in team", phase.name)
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
            key=lambda agent: expertise_profiles[getattr(agent, "name", str(id(agent)))][
                RoleName.PRIMUS
            ],
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
            profile[role] = sum(1 for keyword in keywords for item in expertise if keyword.lower() in item.lower())
        return profile

    def _calculate_expertise_score(self, agent: SupportsTeamAgent, task: TaskDict) -> int:
        expertise = getattr(agent, "expertise", None) or []
        if not expertise:
            return 0
        keywords = _extract_task_keywords(task)
        score = 0
        for item in expertise:
            lower_item = item.lower()
            score += sum(1 for keyword in keywords if keyword in lower_item or lower_item in keyword)
        return score

    def _calculate_phase_expertise(
        self, agent: SupportsTeamAgent, task: TaskDict, phase_keywords: Sequence[str]
    ) -> int:
        base = self._calculate_expertise_score(agent, task)
        expertise = getattr(agent, "expertise", None) or []
        phase_score = 0
        for item in expertise:
            lower_item = item.lower()
            phase_score += sum(1 for keyword in phase_keywords if keyword in lower_item or lower_item in keyword)
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
    self: WSDETeam, role_mapping: Optional[Mapping[str | RoleName, SupportsTeamAgent]] = None
) -> RoleAssignments:
    return _manager(self).assign(role_mapping)


def assign_roles_for_phase(self: WSDETeam, phase: Phase, task: TaskDict) -> RoleAssignments:
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


def _calculate_expertise_score(self: WSDETeam, agent: SupportsTeamAgent, task: TaskDict) -> int:
    return _manager(self)._calculate_expertise_score(agent, task)


def _calculate_phase_expertise_score(
    self: WSDETeam, agent: SupportsTeamAgent, task: TaskDict, phase_keywords: Sequence[str]
) -> int:
    return _manager(self)._calculate_phase_expertise(agent, task, phase_keywords)


def select_primus_by_expertise(self: WSDETeam, task: TaskDict) -> SupportsTeamAgent | None:
    return _manager(self).select_primus_by_expertise(task)


def rotate_roles(self: WSDETeam) -> RoleAssignments:
    return _manager(self).rotate()


def select_primus_for_persona(
    self: WSDETeam, task: TaskDict, persona: str | ResearchPersonaDefinition
) -> SupportsTeamAgent | None:
    definition = (
        persona
        if isinstance(persona, ResearchPersonaDefinition)
        else get_research_persona(str(persona))
    )
    return _manager(self).select_primus_for_persona(task, definition)


def _assign_roles_for_edrr_phase(self: WSDETeam, phase: Phase, task: TaskDict) -> RoleAssignments:
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
]

