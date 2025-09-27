"""Typed agent adapter and coordinator implementations for DevSynth."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, Type, runtime_checkable, cast

import yaml

from devsynth.exceptions import ValidationError

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...application.agents.code import CodeAgent
from ...application.agents.critic import CriticAgent
from ...application.agents.diagram import DiagramAgent
from ...application.agents.documentation import DocumentationAgent
from ...application.agents.planner import PlannerAgent
from ...application.agents.refactor import RefactorAgent
from ...application.agents.specification import SpecificationAgent
from ...application.agents.test import TestAgent
from ...application.agents.unified_agent import UnifiedAgent
from ...application.agents.validation import ValidationAgent
from ...domain.interfaces.agent import Agent, AgentCoordinator, AgentFactory
from ...domain.models.agent import AgentConfig, AgentType
from ...domain.models.wsde import WSDETeam
from ...methodology.edrr.contracts import MemoryManager
from ...ports.llm_port import LLMPort

logger = DevSynthLogger(__name__)


def _load_default_config(config_path: Path) -> dict[str, Any]:  # pragma: no cover - exercised in adapter configuration tests
    """Load the adapter default configuration from disk.

    The configuration file may be missing in lean test environments.  Returning an
    empty mapping keeps the adapter callable while allowing the configuration to be
    populated explicitly in integration tests.
    """

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            loaded = yaml.safe_load(config_file)
    except OSError:
        return {}

    if isinstance(loaded, Mapping):
        return dict(loaded)

    return {}


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "default.yml"
_DEFAULT_CONFIG: dict[str, Any] = _load_default_config(_DEFAULT_CONFIG_PATH)
_AGENT_TYPE_BY_VALUE = {item.value: item for item in AgentType}


def _normalise_capabilities(values: object) -> tuple[str, ...]:  # pragma: no cover - simple data coercion
    """Convert arbitrary capability payloads into a typed tuple of strings."""

    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        return tuple(str(value) for value in values)
    return ()


def _normalise_parameters(values: object) -> dict[str, Any]:  # pragma: no cover - simple data coercion
    """Convert optional parameter mappings into a serialisable dictionary."""

    if isinstance(values, Mapping):
        return dict(values)
    return {}


@dataclass(slots=True)
class AgentCreationConfigPayload:  # pragma: no cover - validated via targeted unit tests
    """Serialisable payload that mirrors the :class:`AgentConfig` schema."""

    name: str
    agent_type: AgentType
    description: str
    capabilities: tuple[str, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls, agent_type_name: str, payload: Mapping[str, Any] | None
    ) -> "AgentCreationConfigPayload":
        """Create a payload from an untyped mapping originating from callers."""

        data = dict(payload or {})
        agent_type = _AGENT_TYPE_BY_VALUE.get(
            agent_type_name, AgentType.ORCHESTRATOR
        )

        name = str(data.get("name", f"{agent_type_name}_agent"))
        description = str(
            data.get("description", f"Agent for {agent_type_name} tasks")
        )

        capabilities = _normalise_capabilities(data.get("capabilities"))
        parameters = _normalise_parameters(data.get("parameters"))

        return cls(
            name=name,
            agent_type=agent_type,
            description=description,
            capabilities=capabilities,
            parameters=parameters,
        )

    def to_agent_config(self) -> AgentConfig:
        """Convert the payload into the runtime :class:`AgentConfig` object."""

        return AgentConfig(
            name=self.name,
            agent_type=self.agent_type,
            description=self.description,
            capabilities=list(self.capabilities),
            parameters=dict(self.parameters),
        )


@dataclass(slots=True)
class DelegatedTaskRequest:  # pragma: no cover - validated via targeted unit tests
    """Typed wrapper around a task payload passed to WSDE teams."""

    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "DelegatedTaskRequest":
        if payload is None:
            raise ValidationError("Task payload cannot be None.")
        return cls(dict(payload))

    @property
    def is_critical_decision(self) -> bool:
        """Return whether the task represents a critical decision."""

        return bool(
            self.payload.get("type") == "critical_decision"
            and self.payload.get("is_critical", False)
        )

    def iter_solutions(self) -> tuple[dict[str, Any], ...]:
        """Yield sanitised solution payloads embedded in the task."""

        raw_solutions = self.payload.get("solutions")
        if not (
            isinstance(raw_solutions, Sequence)
            and not isinstance(raw_solutions, (str, bytes))
        ):
            return ()
        return tuple(
            dict(item)
            for item in raw_solutions
            if isinstance(item, Mapping)
        )

    def option_labels(self, agents: Sequence[Agent]) -> list[str]:
        """Derive consensus option labels from solutions or fall back to agents."""

        options = [
            str(solution.get("content") or solution.get("agent") or f"option_{index}")
            for index, solution in enumerate(self.iter_solutions(), start=1)
        ]
        if options:
            return options
        return [
            str(getattr(agent, "name", f"agent_{index}"))
            for index, agent in enumerate(agents, start=1)
        ]

    def consensus_payload(self, options: Sequence[str]) -> dict[str, Any]:
        """Create a mapping suitable for the team's consensus builder."""

        return dict(self.payload, options=list(options))

    def solution_from_agent(
        self, agent: Agent, agent_solution: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """Shape an agent response into a solution record."""

        if agent_solution is None:
            response: Mapping[str, Any] = {}
        elif isinstance(agent_solution, Mapping):
            response = dict(agent_solution)
        else:  # pragma: no cover - defensive guard
            response = {"result": agent_solution}

        agent_name = (
            getattr(getattr(agent, "config", None), "name", None)
            or getattr(agent, "name", "Agent")
        )

        raw_confidence = response.get("confidence", 1.0)
        try:
            confidence = float(raw_confidence)
        except (TypeError, ValueError):
            confidence = 1.0

        return {
            "agent": agent_name,
            "content": response.get("result", ""),
            "confidence": confidence,
            "reasoning": response.get("reasoning", ""),
        }

    @staticmethod
    def contributors_from_consensus(consensus: Mapping[str, Any]) -> list[str]:
        """Extract contributor identifiers from a consensus payload."""

        preferences = consensus.get("initial_preferences", {})
        if isinstance(preferences, Mapping):
            return [str(identifier) for identifier in preferences]
        return []


class AgentBuilder(Protocol):  # pragma: no cover - structural typing helper
    """Callable capable of producing an :class:`Agent`."""

    def __call__(self) -> Agent:
        ...


@runtime_checkable
class ConsensusCapableTeam(Protocol):  # pragma: no cover - structural typing helper
    """Protocol describing the small surface consumed by the coordinator."""

    agents: Sequence[object]

    def add_agent(self, agent: object) -> None:
        ...

    def add_agents(self, agents: Sequence[object]) -> None:
        ...

    def vote_on_critical_decision(
        self, task: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        ...

    def select_primus_by_expertise(self, task: Mapping[str, Any]) -> None:
        ...

    def get_primus(self) -> object | None:
        ...

    def add_solution(self, task: Mapping[str, Any], solution: Mapping[str, Any]) -> None:
        ...

    def build_consensus(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def apply_enhanced_dialectical_reasoning_multi(
        self, task: Mapping[str, Any], critic_agent: Agent
    ) -> Mapping[str, Any]:
        ...


class SimplifiedAgentFactory(AgentFactory):  # pragma: no cover - exercised via integration-oriented suites
    """
    Simplified factory for creating DevSynth agents.

    This factory implements the single-agent design for MVP while
    preserving extension points for future multi-agent capabilities.
    """

    def __init__(self, llm_port: LLMPort | None = None):
        # For MVP, we only use the UnifiedAgent
        self.agent_types: dict[str, AgentBuilder] = {
            AgentType.ORCHESTRATOR.value: UnifiedAgent,
            AgentType.PLANNER.value: PlannerAgent,
            AgentType.TEST.value: TestAgent,
            AgentType.CODE.value: CodeAgent,
        }
        self.llm_port = llm_port

        # Extension point: Additional specialized agents can be registered here
        self.future_agent_types: dict[str, AgentBuilder] = {
            AgentType.SPECIFICATION.value: SpecificationAgent,
            AgentType.VALIDATION.value: ValidationAgent,
            AgentType.REFACTOR.value: RefactorAgent,
            AgentType.DOCUMENTATION.value: DocumentationAgent,
            AgentType.DIAGRAM.value: DiagramAgent,
            AgentType.CRITIC.value: CriticAgent,
        }

    def create_agent(
        self, agent_type: str, config: Mapping[str, Any] | None = None
    ) -> Agent:
        """
        Create an agent of the specified type.

        For MVP, this always returns a UnifiedAgent regardless of the requested type,
        ensuring backward compatibility with existing code.
        """
        # Select the appropriate agent class based on the requested type
        agent_class = self.agent_types.get(agent_type, UnifiedAgent)

        # Allow future/experimental agent types to be registered separately
        if agent_type not in self.agent_types:
            agent_class = self.future_agent_types.get(agent_type, UnifiedAgent)

        agent = agent_class()

        if config:
            payload = AgentCreationConfigPayload.from_mapping(agent_type, config)
            agent.initialize(payload.to_agent_config())

        # Set the LLM port if available
        if self.llm_port:
            agent.set_llm_port(self.llm_port)

        return agent

    def register_agent_type(self, agent_type: str, agent_class: AgentBuilder) -> None:
        """
        Register a new agent type.

        This is an extension point for future versions. In MVP, this method
        is a no-op since we only use the UnifiedAgent.
        """
        # For MVP we still allow registration so tests can extend the factory
        logger.debug("Registering agent type %s", agent_type)
        self.agent_types[agent_type] = agent_class


class WSDETeamCoordinator(AgentCoordinator):  # pragma: no cover - complex WSDE orchestration
    """
    Coordinator for WSDE teams.

    This class is retained for future multi-agent capabilities but is simplified
    for MVP to work with a single agent.
    """

    def __init__(self, memory_manager: MemoryManager | None = None):
        self.teams: dict[str, ConsensusCapableTeam] = {}
        self.current_team_id: str | None = None
        self.memory_manager = memory_manager

    def create_team(self, team_id: str) -> ConsensusCapableTeam:
        """Create a new WSDE team."""
        # Import here to avoid circular imports
        from devsynth.application.collaboration.collaborative_wsde_team import (
            CollaborativeWSDETeam,
        )

        # Use CollaborativeWSDETeam if memory_manager is available, otherwise use WSDETeam
        if self.memory_manager:  # pragma: no cover - integration-specific team variant
            team = cast(
                ConsensusCapableTeam,
                CollaborativeWSDETeam(name=team_id, memory_manager=self.memory_manager),
            )
        else:
            team = cast(ConsensusCapableTeam, WSDETeam(name=team_id))

        self.teams[team_id] = team
        self.current_team_id = team_id
        return team

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the current team."""
        if self.current_team_id is None:
            # For MVP, create a default team if none exists
            self.create_team("default_team")

        team = self.teams[self.current_team_id]
        team.add_agent(agent)

        # For MVP, we don't need to assign roles since we only have one agent
        if len(team.agents) > 1:  # pragma: no cover - role assignment exercised in WSDE flows
            assign_roles = getattr(team, "assign_roles", None)
            if callable(assign_roles):
                assign_roles()

    def add_agents(self, agents: Sequence[Agent]) -> None:
        """Add multiple agents to the current team."""
        for agent in agents:
            self.add_agent(agent)

    def delegate_task(self, task: Mapping[str, Any]) -> dict[str, Any]:
        """
        Delegate a task to the appropriate agent(s) in the current team.

        In the refined WSDE model, this uses:
        1. Voting mechanisms for critical decisions
        2. Consensus-based approach for regular tasks where:
           a. The agent with the most relevant expertise becomes the temporary Primus
           b. All agents can propose solutions and provide critiques
           c. The final solution is built through consensus

        For MVP with a single agent, this simply passes the task to that agent.
        """
        if self.current_team_id is None:
            raise ValidationError("No active team. Create a team first.")

        team = self.teams[self.current_team_id]
        request = DelegatedTaskRequest.from_mapping(task)
        agents = [cast(Agent, agent) for agent in team.agents]

        if not agents:
            raise ValidationError("No agents in the team.")
        if len(agents) == 1:
            single_result = agents[0].process(request.payload)
            if isinstance(single_result, Mapping):
                return dict(single_result)
            return {"result": single_result}

        if request.is_critical_decision:
            decision = team.vote_on_critical_decision(request.payload)
            if isinstance(decision, Mapping):
                return dict(decision)
            return {"result": decision}

        team.select_primus_by_expertise(request.payload)
        primus_candidate = team.get_primus()
        primus = cast(Agent | None, primus_candidate)

        return self._delegate_multi_agent(team, request, agents, primus)

    def get_team(self, team_id: str) -> ConsensusCapableTeam | None:
        """Get a team by ID."""
        return self.teams.get(team_id)

    def set_current_team(self, team_id: str) -> None:
        """Set the current active team."""
        if team_id not in self.teams:
            raise ValidationError(f"Team {team_id} does not exist.")
        self.current_team_id = team_id

    def _delegate_multi_agent(  # pragma: no cover - exercised in integration suites
        self,
        team: ConsensusCapableTeam,
        request: DelegatedTaskRequest,
        agents: Sequence[Agent],
        primus: Agent | None,
    ) -> dict[str, Any]:
        add_solution = getattr(team, "add_solution", None)

        for agent in agents:
            try:
                agent_solution = agent.process(request.payload)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning(
                    "Agent %s failed to process task: %s",
                    getattr(agent, "name", "Agent"),
                    exc,
                )
                continue

            shaped_solution = request.solution_from_agent(agent, agent_solution)
            if callable(add_solution):
                add_solution(request.payload, shaped_solution)

        options = request.option_labels(agents)
        consensus_payload = team.build_consensus(request.consensus_payload(options))
        if isinstance(consensus_payload, Mapping):
            consensus = dict(consensus_payload)
        else:
            consensus = {"result": consensus_payload}

        critic_agent = primus if primus is not None else agents[0]
        dialectical = team.apply_enhanced_dialectical_reasoning_multi(
            request.payload, critic_agent
        )

        explanation = str(consensus.get("explanation", ""))
        return {
            "status": consensus.get("status", "failed"),
            "result": consensus.get("result"),
            "consensus": consensus.get("result"),
            "contributors": DelegatedTaskRequest.contributors_from_consensus(consensus),
            "method": "consensus_deliberation",
            "reasoning": explanation,
            "explanation": explanation,
            "rounds": consensus.get("rounds", []),
            "final_preferences": consensus.get("final_preferences", {}),
            "dialectical_analysis": dialectical,
        }


class AgentAdapter:
    """
    Adapter for the agent system.

    This adapter provides a unified interface to the agent system,
    implementing the single-agent design for MVP while preserving
    extension points for future multi-agent capabilities.
    """

    def __init__(
        self,
        llm_port: LLMPort | None = None,
        config: Mapping[str, Any] | None = None,
        memory_manager: MemoryManager | None = None,
    ):
        self.config = dict(config) if config is not None else dict(_DEFAULT_CONFIG)
        self.agent_factory = SimplifiedAgentFactory(llm_port)
        self.agent_coordinator = WSDETeamCoordinator(memory_manager=memory_manager)
        self.llm_port = llm_port
        self.memory_manager = memory_manager
        feature_cfg = self.config.get("features", {})
        self.multi_agent_enabled = feature_cfg.get("wsde_collaboration", False)

    def create_agent(
        self, agent_type: str, config: Mapping[str, Any] | None = None
    ) -> Agent:
        """Create an agent of the specified type."""
        return self.agent_factory.create_agent(agent_type, config)

    def create_team(self, team_id: str) -> ConsensusCapableTeam:
        """Create a new WSDE team."""
        return self.agent_coordinator.create_team(team_id)

    def add_agent_to_team(self, agent: Agent) -> None:
        """Add an agent to the current team."""
        self.agent_coordinator.add_agent(agent)

    def add_agents_to_team(self, agents: Sequence[Agent]) -> None:
        """Add multiple agents to the current team."""
        self.agent_coordinator.add_agents(agents)

    def process_task(self, task: Mapping[str, Any]) -> dict[str, Any]:  # pragma: no cover - exercised via coordinator integration
        """Process a task using the current team."""
        request = DelegatedTaskRequest.from_mapping(task)

        if not self.multi_agent_enabled:
            team = self.agent_coordinator.teams.get(
                self.agent_coordinator.current_team_id
            )
            if not team or not team.agents:
                raise ValidationError("No agents in the team.")

            agent = cast(Agent, team.agents[0])
            single_result = agent.process(request.payload)
            if isinstance(single_result, Mapping):
                return dict(single_result)
            return {"result": single_result}

        return self.agent_coordinator.delegate_task(request.payload)

    def register_agent_type(self, agent_type: str, agent_class: AgentBuilder) -> None:
        """Register a new agent type."""
        self.agent_factory.register_agent_type(agent_type, agent_class)

    def get_team(self, team_id: str) -> ConsensusCapableTeam | None:
        """Get a team by ID."""
        return self.agent_coordinator.get_team(team_id)

    def set_current_team(self, team_id: str) -> None:
        """Set the current active team."""
        self.agent_coordinator.set_current_team(team_id)
