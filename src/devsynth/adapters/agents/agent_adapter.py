"""Adapter entry-points for DevSynth agents.

This module wires runtime adapters into the application-layer agent
implementations. The strict typing workstream tightens the protocol
surface so adapters can evolve without reintroducing ``Any`` fallbacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import (
    Any,
    Final,
    TypedDict,
    cast,
)
from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence

from devsynth.exceptions import ValidationError
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.agent import Agent, AgentCoordinator, AgentFactory
from ...domain.models.agent import AgentConfig, AgentType
from ...domain.models.wsde import WSDETeam
from ...methodology.edrr.contracts import MemoryManager as MemoryManagerProtocol
from ...ports.llm_port import LLMPort

logger = DevSynthLogger(__name__)


class TaskSolution(TypedDict, total=False):
    """Typed representation of solutions accumulated during delegation."""

    agent: str
    content: str
    confidence: float
    reasoning: str


class TaskPayload(TypedDict, total=False):
    """Minimal task contract understood by the coordinator."""

    type: str
    is_critical: bool
    solutions: list[TaskSolution]
    options: list[str]


@dataclass(slots=True)
class AgentInitializationPayload:
    """Normalized data used to initialize an agent."""

    name: str
    agent_type: AgentType
    description: str
    capabilities: list[str]
    parameters: dict[str, Any]

    @classmethod
    def from_mapping(
        cls, payload: Mapping[str, Any], requested_type: str
    ) -> AgentInitializationPayload:
        """Coerce loosely-typed config dictionaries into a structured payload."""

        description = str(
            payload.get("description", f"Agent for {requested_type} tasks")
        )
        capabilities = _coerce_str_sequence(payload.get("capabilities"))
        parameters = _coerce_mapping(payload.get("parameters"))
        agent_name = str(payload.get("name", f"{requested_type}_agent"))

        try:
            normalized_type = AgentType(requested_type)
        except ValueError:
            normalized_type = AgentType.ORCHESTRATOR

        return cls(
            name=agent_name,
            agent_type=normalized_type,
            description=description,
            capabilities=capabilities,
            parameters=parameters,
        )


class _UnifiedAgentFallback:
    """Lightweight fallback agent used when optional imports are unavailable."""

    def __init__(self) -> None:
        self.config: AgentConfig | None = None
        self.llm_port: LLMPort | None = None

    def initialize(self, config: AgentConfig) -> None:
        self.config = config

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "result": inputs.get("result", inputs)}

    def get_capabilities(self) -> list[str]:
        return []

    def set_llm_port(self, llm_port: LLMPort) -> None:
        self.llm_port = llm_port


def _coerce_mapping(value: Any) -> dict[str, Any]:
    """Best-effort coercion of mapping-like inputs to ``dict``."""

    if isinstance(value, Mapping):
        return {str(key): value[key] for key in value}
    return {}


def _coerce_str_sequence(value: Any) -> list[str]:
    """Return a list of strings when the input is a non-string sequence."""

    if isinstance(value, Sequence) and not isinstance(value, (bytes, str)):
        return [str(item) for item in value]
    if isinstance(value, Iterable) and not isinstance(value, (bytes, str)):
        return [str(item) for item in value]
    return []


def _coerce_task_solutions(value: Any) -> list[TaskSolution]:
    """Normalize task solutions to the :class:`TaskSolution` contract."""

    if not isinstance(value, Sequence) or isinstance(value, (bytes, str)):
        return []

    solutions: list[TaskSolution] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            continue

        solution = TaskSolution()
        agent = entry.get("agent")
        if agent is not None:
            solution["agent"] = str(agent)

        content = entry.get("content")
        if content is not None:
            solution["content"] = str(content)

        confidence = entry.get("confidence")
        if isinstance(confidence, (int, float)):
            solution["confidence"] = float(confidence)

        reasoning = entry.get("reasoning")
        if reasoning is not None:
            solution["reasoning"] = str(reasoning)

        solutions.append(solution)
    return solutions


def _load_default_config(config_path: Path) -> dict[str, Any]:
    """Load the default YAML configuration used by the adapter."""

    try:
        yaml_module = import_module("yaml")
    except ImportError:  # pragma: no cover - optional dependency guard
        logger.debug("PyYAML not installed; skipping default adapter config load")
        return {}

    safe_load = getattr(yaml_module, "safe_load", None)
    if not callable(safe_load):
        logger.debug("yaml.safe_load unavailable; skipping default adapter config load")
        return {}

    loader = cast(Callable[[Any], Any], safe_load)

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = loader(handle) or {}
    except Exception as error:  # pragma: no cover - defensive guard
        logger.debug("Failed to load default adapter config", exc_info=error)
        return {}

    if not isinstance(data, Mapping):
        return {}
    return dict(cast(Mapping[str, Any], data))


_DEFAULT_CONFIG_PATH: Final = (
    Path(__file__).resolve().parents[3] / "config" / "default.yml"
)
_DEFAULT_CONFIG: Final[dict[str, Any]] = _load_default_config(_DEFAULT_CONFIG_PATH)


def _import_agent(module_path: str, attr: str, fallback: type[Agent]) -> type[Agent]:
    """Best-effort import for optional agent classes."""

    try:
        module = import_module(module_path)
        candidate = getattr(module, attr)
    except Exception as error:  # pragma: no cover - optional dependency guard
        logger.debug(
            "Falling back to %s for %s.%s: %s",
            fallback.__name__,
            module_path,
            attr,
            error,
        )
        return fallback

    if isinstance(candidate, type):
        return cast(type[Agent], candidate)

    logger.debug(
        "Attribute %s.%s is not a class; using %s fallback",
        module_path,
        attr,
        fallback.__name__,
    )
    return fallback


DEFAULT_AGENT_CLASS: type[Agent] = _import_agent(
    "devsynth.application.agents.unified_agent",
    "UnifiedAgent",
    _UnifiedAgentFallback,
)


class SimplifiedAgentFactory:
    """
    Simplified factory for creating DevSynth agents.

    This factory implements the single-agent design for MVP while
    preserving extension points for future multi-agent capabilities.
    """

    def __init__(self, llm_port: LLMPort | None = None):
        # For MVP, we only use the UnifiedAgent
        self.llm_port: LLMPort | None = llm_port
        self._agent_specs: dict[str, tuple[str, str]] = {
            AgentType.PLANNER.value: (
                "devsynth.application.agents.planner",
                "PlannerAgent",
            ),
            AgentType.TEST.value: (
                "devsynth.application.agents.test",
                "TestAgent",
            ),
            AgentType.CODE.value: (
                "devsynth.application.agents.code",
                "CodeAgent",
            ),
        }
        self._future_agent_specs: dict[str, tuple[str, str]] = {
            AgentType.SPECIFICATION.value: (
                "devsynth.application.agents.specification",
                "SpecificationAgent",
            ),
            AgentType.VALIDATION.value: (
                "devsynth.application.agents.validation",
                "ValidationAgent",
            ),
            AgentType.REFACTOR.value: (
                "devsynth.application.agents.refactor",
                "RefactorAgent",
            ),
            AgentType.DOCUMENTATION.value: (
                "devsynth.application.agents.documentation",
                "DocumentationAgent",
            ),
            AgentType.DIAGRAM.value: (
                "devsynth.application.agents.diagram",
                "DiagramAgent",
            ),
            AgentType.CRITIC.value: (
                "devsynth.application.agents.critic",
                "CriticAgent",
            ),
        }
        self._resolved_agent_types: dict[str, type[Agent]] = {
            AgentType.ORCHESTRATOR.value: DEFAULT_AGENT_CLASS
        }
        self._custom_agents: dict[str, type[Agent]] = {}

    def create_agent(
        self, agent_type: str, config: Mapping[str, Any] | None = None
    ) -> Agent:
        """
        Create an agent of the specified type.

        For MVP, this always returns a UnifiedAgent regardless of the requested type,
        ensuring backward compatibility with existing code.
        """
        # Select the appropriate agent class based on the requested type
        agent_class = self._lookup_agent_class(agent_type)

        agent = cast(Agent, agent_class())

        if config:
            # Use the requested agent_type for backward compatibility
            payload = AgentInitializationPayload.from_mapping(config, agent_type)
            agent_config = AgentConfig(
                name=payload.name,
                agent_type=payload.agent_type,
                description=payload.description,
                capabilities=list(payload.capabilities),
                parameters=dict(payload.parameters),
            )
            agent.initialize(agent_config)

        # Set the LLM port if available
        if self.llm_port:
            agent.set_llm_port(self.llm_port)

        return agent

    def register_agent_type(self, agent_type: str, agent_class: type[Agent]) -> None:
        """
        Register a new agent type.

        This is an extension point for future versions. In MVP, this method
        is a no-op since we only use the UnifiedAgent.
        """
        # For MVP we still allow registration so tests can extend the factory
        logger.debug("Registering agent type %s", agent_type)
        self._custom_agents[agent_type] = agent_class
        self._resolved_agent_types.pop(agent_type, None)

    def _lookup_agent_class(self, agent_type: str) -> type[Agent]:
        if agent_type in self._custom_agents:
            return self._custom_agents[agent_type]
        if agent_type in self._resolved_agent_types:
            return self._resolved_agent_types[agent_type]

        if agent_type in self._agent_specs:
            module_path, attr = self._agent_specs[agent_type]
            resolved = _import_agent(module_path, attr, DEFAULT_AGENT_CLASS)
            self._resolved_agent_types[agent_type] = resolved
            return resolved

        if agent_type in self._future_agent_specs:
            module_path, attr = self._future_agent_specs[agent_type]
            resolved = _import_agent(module_path, attr, DEFAULT_AGENT_CLASS)
            self._resolved_agent_types[agent_type] = resolved
            return resolved

        return DEFAULT_AGENT_CLASS


class WSDETeamCoordinator:
    """
    Coordinator for WSDE teams.

    This class is retained for future multi-agent capabilities but is simplified
    for MVP to work with a single agent.
    """

    def __init__(self, memory_manager: MemoryManagerProtocol | None = None):
        self.teams: dict[str, WSDETeam] = {}
        self.current_team_id: str | None = None
        self.memory_manager: MemoryManagerProtocol | None = memory_manager

    def create_team(self, team_id: str) -> WSDETeam:
        """Create a new WSDE team."""
        # Import here to avoid circular imports
        from devsynth.application.collaboration.collaborative_wsde_team import (
            CollaborativeWSDETeam,
        )

        # Use CollaborativeWSDETeam if memory_manager is available, otherwise use WSDETeam
        if self.memory_manager:
            team = CollaborativeWSDETeam(
                name=team_id, memory_manager=self.memory_manager
            )
        else:
            team = WSDETeam(name=team_id)

        self.teams[team_id] = team
        self.current_team_id = team_id
        return team

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the current team."""
        if self.current_team_id is None:
            # For MVP, create a default team if none exists
            self.create_team("default_team")

        team_id = self.current_team_id
        if team_id is None:  # pragma: no cover - defensive fallback
            raise ValidationError("No active team. Create a team first.")

        team = self.teams[team_id]
        team.add_agent(agent)

        # For MVP, we don't need to assign roles since we only have one agent
        if len(team.agents) > 1:
            team.assign_roles()

    def add_agents(self, agents: Iterable[Agent]) -> None:
        """Add multiple agents to the current team."""
        for agent in agents:
            self.add_agent(agent)

    def delegate_task(
        self, task: MutableMapping[str, Any] | TaskPayload
    ) -> dict[str, Any]:
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
        task_mapping = cast(MutableMapping[str, Any], task)

        team_id = self.current_team_id
        if team_id is None:
            raise ValidationError("No active team. Create a team first.")

        team = self.teams[team_id]

        # For MVP with a single agent
        if len(team.agents) == 0:
            raise ValidationError("No agents in the team.")
        elif len(team.agents) == 1:
            # Just use the single agent
            agent = team.agents[0]
            return cast(dict[str, Any], agent.process(dict(task_mapping)))

        # For multi-agent teams, use the refined WSDE model

        # Check if this is a critical decision task
        if task_mapping.get("type") == "critical_decision" and bool(
            task_mapping.get("is_critical", False)
        ):
            # Use voting mechanisms for critical decisions
            vote_result = team.vote_on_critical_decision(task_mapping)
            return cast(dict[str, Any], vote_result)

        # For regular tasks, use consensus-based approach

        # 1. Select the agent with the most relevant expertise as Primus
        team.select_primus_by_expertise(task_mapping)
        primus = team.get_primus()

        solutions = _coerce_task_solutions(task_mapping.get("solutions"))
        task_mapping["solutions"] = solutions

        # 2. Have all agents process the task and propose solutions
        for agent in team.agents:
            try:
                agent_solution = agent.process(dict(task_mapping))
            except Exception as e:
                logger.warning(
                    f"Agent {getattr(agent, 'name', 'Agent')} failed to process task: {e}"
                )
                continue

            agent_name = (
                agent.config.name
                if hasattr(agent, "config") and hasattr(agent.config, "name")
                else agent.name if hasattr(agent, "name") else "Agent"
            )
            confidence_raw = agent_solution.get("confidence", 1.0)
            confidence = (
                float(confidence_raw)
                if isinstance(confidence_raw, (int, float))
                else 1.0
            )
            solution: TaskSolution = {
                "agent": agent_name,
                "content": str(agent_solution.get("result", "")),
                "confidence": confidence,
                "reasoning": str(agent_solution.get("reasoning", "")),
            }
            team.add_solution(task_mapping, solution)

        # 3. Have agents critique each other's solutions
        # This is handled implicitly by the build_consensus method,
        # which analyzes and compares all solutions

        # 4. Build consensus through deliberation
        options: list[str] = []
        for idx, solution in enumerate(solutions, start=1):
            descriptor = solution.get("content") or solution.get("agent")
            if not descriptor:
                descriptor = f"option_{idx}"
            options.append(descriptor)

        if not options:
            options = [
                getattr(agent, "name", f"agent_{idx}")
                for idx, agent in enumerate(team.agents, start=1)
            ]

        consensus_payload = dict(task_mapping)
        consensus_payload["options"] = options
        consensus = cast(dict[str, Any], team.build_consensus(consensus_payload))

        # 5. Apply dialectical reasoning on the combined solutions
        critic_agent = primus if primus else team.agents[0]
        dialectical = cast(
            dict[str, Any],
            team.apply_enhanced_dialectical_reasoning_multi(task_mapping, critic_agent),
        )

        # 6. Format the result to match the expected output
        contributors = list(consensus.get("initial_preferences", {}).keys())
        explanation = consensus.get("explanation", "")
        return {
            "status": consensus.get("status", "failed"),
            "result": consensus.get("result"),
            "consensus": consensus.get("result"),
            "contributors": contributors,
            "method": "consensus_deliberation",
            "reasoning": explanation,
            "explanation": explanation,
            "rounds": consensus.get("rounds", []),
            "final_preferences": consensus.get("final_preferences", {}),
            "dialectical_analysis": dialectical,
        }

    def get_team(self, team_id: str) -> WSDETeam | None:
        """Get a team by ID."""
        return self.teams.get(team_id)

    def set_current_team(self, team_id: str) -> None:
        """Set the current active team."""
        if team_id not in self.teams:
            raise ValidationError(f"Team {team_id} does not exist.")
        self.current_team_id = team_id


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
        memory_manager: MemoryManagerProtocol | None = None,
    ):
        if config is None:
            self.config: dict[str, Any] = dict(_DEFAULT_CONFIG)
        else:
            self.config = _coerce_mapping(config)
        self.agent_factory = SimplifiedAgentFactory(llm_port)
        self.agent_coordinator = WSDETeamCoordinator(memory_manager=memory_manager)
        self.llm_port: LLMPort | None = llm_port
        self.memory_manager: MemoryManagerProtocol | None = memory_manager
        feature_cfg = _coerce_mapping(self.config.get("features", {}))
        self.multi_agent_enabled = bool(feature_cfg.get("wsde_collaboration", False))

    def create_agent(
        self, agent_type: str, config: Mapping[str, Any] | None = None
    ) -> Agent:
        """Create an agent of the specified type."""
        return self.agent_factory.create_agent(agent_type, config)

    def create_team(self, team_id: str) -> WSDETeam:
        """Create a new WSDE team."""
        return self.agent_coordinator.create_team(team_id)

    def add_agent_to_team(self, agent: Agent) -> None:
        """Add an agent to the current team."""
        self.agent_coordinator.add_agent(agent)

    def add_agents_to_team(self, agents: Iterable[Agent]) -> None:
        """Add multiple agents to the current team."""
        self.agent_coordinator.add_agents(agents)

    def process_task(self, task: MutableMapping[str, Any]) -> dict[str, Any]:
        """Process a task using the current team."""
        if not self.multi_agent_enabled:
            team_id = self.agent_coordinator.current_team_id
            if team_id is None:
                raise ValidationError("No agents in the team.")
            team = self.agent_coordinator.teams.get(team_id)
            if not team or not getattr(team, "agents", []):
                raise ValidationError("No agents in the team.")
            agent = team.agents[0]
            return cast(dict[str, Any], agent.process(dict(task)))

        return self.agent_coordinator.delegate_task(task)

    def register_agent_type(self, agent_type: str, agent_class: type[Agent]) -> None:
        """Register a new agent type."""
        self.agent_factory.register_agent_type(agent_type, agent_class)

    def get_team(self, team_id: str) -> WSDETeam | None:
        """Get a team by ID."""
        return self.agent_coordinator.get_team(team_id)

    def set_current_team(self, team_id: str) -> None:
        """Set the current active team."""
        self.agent_coordinator.set_current_team(team_id)
