"""
Agent adapter for the DevSynth system.
Implements the AgentFactory and AgentCoordinator interfaces.

This implementation focuses on the single-agent design for MVP while
preserving extension points for future multi-agent capabilities.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...application.agents.unified_agent import UnifiedAgent
from ...domain.interfaces.agent import Agent, AgentCoordinator, AgentFactory
from ...domain.models.agent import AgentConfig, AgentType
from ...domain.models.wsde import WSDETeam
from ...ports.llm_port import LLMPort

logger = DevSynthLogger(__name__)
from devsynth.exceptions import ValidationError

# Load default configuration
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "default.yml"
try:
    with open(_DEFAULT_CONFIG_PATH, "r") as f:
        _DEFAULT_CONFIG = yaml.safe_load(f) or {}
except Exception:
    _DEFAULT_CONFIG = {}

# Import specialized agent classes
from ...application.agents.base import BaseAgent
from ...application.agents.code import CodeAgent
from ...application.agents.critic import CriticAgent
from ...application.agents.diagram import DiagramAgent
from ...application.agents.documentation import DocumentationAgent
from ...application.agents.planner import PlannerAgent
from ...application.agents.refactor import RefactorAgent
from ...application.agents.specification import SpecificationAgent
from ...application.agents.test import TestAgent
from ...application.agents.validation import ValidationAgent


class SimplifiedAgentFactory(AgentFactory):
    """
    Simplified factory for creating DevSynth agents.

    This factory implements the single-agent design for MVP while
    preserving extension points for future multi-agent capabilities.
    """

    def __init__(self, llm_port: Optional[LLMPort] = None):
        # For MVP, we only use the UnifiedAgent
        self.agent_types = {
            AgentType.ORCHESTRATOR.value: UnifiedAgent,
            AgentType.PLANNER.value: PlannerAgent,
            AgentType.TEST.value: TestAgent,
            AgentType.CODE.value: CodeAgent,
        }
        self.llm_port = llm_port

        # Extension point: Additional specialized agents can be registered here
        self.future_agent_types = {
            AgentType.SPECIFICATION.value: SpecificationAgent,
            AgentType.VALIDATION.value: ValidationAgent,
            AgentType.REFACTOR.value: RefactorAgent,
            AgentType.DOCUMENTATION.value: DocumentationAgent,
            AgentType.DIAGRAM.value: DiagramAgent,
            AgentType.CRITIC.value: CriticAgent,
        }

    def create_agent(self, agent_type: str, config: Dict[str, Any] = None) -> Agent:
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
            # Use the requested agent_type for backward compatibility
            agent_config = AgentConfig(
                name=config.get("name", f"{agent_type}_agent"),
                agent_type=(
                    AgentType(agent_type)
                    if agent_type in [e.value for e in AgentType]
                    else AgentType.ORCHESTRATOR
                ),
                description=config.get("description", f"Agent for {agent_type} tasks"),
                capabilities=config.get("capabilities", []),
                parameters=config.get("parameters", {}),
            )
            agent.initialize(agent_config)

        # Set the LLM port if available
        if self.llm_port:
            agent.set_llm_port(self.llm_port)

        return agent

    def register_agent_type(self, agent_type: str, agent_class: Type) -> None:
        """
        Register a new agent type.

        This is an extension point for future versions. In MVP, this method
        is a no-op since we only use the UnifiedAgent.
        """
        # For MVP we still allow registration so tests can extend the factory
        logger.debug("Registering agent type %s", agent_type)
        self.agent_types[agent_type] = agent_class


class WSDETeamCoordinator(AgentCoordinator):
    """
    Coordinator for WSDE teams.

    This class is retained for future multi-agent capabilities but is simplified
    for MVP to work with a single agent.
    """

    def __init__(self, memory_manager=None):
        self.teams = {}  # Dictionary of teams by team_id
        self.current_team_id = None
        self.memory_manager = memory_manager

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

        team = self.teams[self.current_team_id]
        team.add_agent(agent)

        # For MVP, we don't need to assign roles since we only have one agent
        if len(team.agents) > 1:
            team.assign_roles()

    def add_agents(self, agents: List[Agent]) -> None:
        """Add multiple agents to the current team."""
        for agent in agents:
            self.add_agent(agent)

    def delegate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
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

        # For MVP with a single agent
        if len(team.agents) == 0:
            raise ValidationError("No agents in the team.")
        elif len(team.agents) == 1:
            # Just use the single agent
            agent = team.agents[0]
            return agent.process(task)

        # For multi-agent teams, use the refined WSDE model

        # Check if this is a critical decision task
        if task.get("type") == "critical_decision" and task.get("is_critical", False):
            # Use voting mechanisms for critical decisions
            return team.vote_on_critical_decision(task)

        # For regular tasks, use consensus-based approach

        # 1. Select the agent with the most relevant expertise as Primus
        team.select_primus_by_expertise(task)
        primus = team.get_primus()

        # 2. Have all agents process the task and propose solutions
        for agent in team.agents:
            try:
                agent_solution = agent.process(task)
            except Exception as e:
                logger.warning(
                    f"Agent {getattr(agent, 'name', 'Agent')} failed to process task: {e}"
                )
                continue

            solution = {
                "agent": (
                    agent.config.name
                    if hasattr(agent, "config") and hasattr(agent.config, "name")
                    else agent.name if hasattr(agent, "name") else "Agent"
                ),
                "content": agent_solution.get("result", ""),
                "confidence": agent_solution.get("confidence", 1.0),
                "reasoning": agent_solution.get("reasoning", ""),
            }
            team.add_solution(task, solution)

        # 3. Have agents critique each other's solutions
        # This is handled implicitly by the build_consensus method,
        # which analyzes and compares all solutions

        # 4. Build consensus through deliberation
        consensus = team.build_consensus(task)

        # 5. Apply dialectical reasoning on the combined solutions
        critic_agent = primus if primus else team.agents[0]
        dialectical = team.apply_enhanced_dialectical_reasoning_multi(
            task, critic_agent
        )

        # 6. Format the result to match the expected output
        return {
            "result": consensus.get("consensus", ""),
            "contributors": consensus.get("contributors", []),
            "method": consensus.get("method", "consensus"),
            "reasoning": consensus.get("reasoning", ""),
            "dialectical_analysis": dialectical,
        }

    def get_team(self, team_id: str) -> Optional[WSDETeam]:
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
        llm_port: Optional[LLMPort] = None,
        config: Optional[Dict[str, Any]] = None,
        memory_manager=None,
    ):
        self.config = config or _DEFAULT_CONFIG
        self.agent_factory = SimplifiedAgentFactory(llm_port)
        self.agent_coordinator = WSDETeamCoordinator(memory_manager=memory_manager)
        self.llm_port = llm_port
        self.memory_manager = memory_manager
        feature_cfg = self.config.get("features", {})
        self.multi_agent_enabled = feature_cfg.get("wsde_collaboration", False)

    def create_agent(self, agent_type: str, config: Dict[str, Any] = None) -> Agent:
        """Create an agent of the specified type."""
        return self.agent_factory.create_agent(agent_type, config)

    def create_team(self, team_id: str) -> WSDETeam:
        """Create a new WSDE team."""
        return self.agent_coordinator.create_team(team_id)

    def add_agent_to_team(self, agent: Agent) -> None:
        """Add an agent to the current team."""
        self.agent_coordinator.add_agent(agent)

    def add_agents_to_team(self, agents: List[Agent]) -> None:
        """Add multiple agents to the current team."""
        self.agent_coordinator.add_agents(agents)

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task using the current team."""
        if not self.multi_agent_enabled:
            team = self.agent_coordinator.teams.get(
                self.agent_coordinator.current_team_id
            )
            if not team or not team.agents:
                raise ValidationError("No agents in the team.")
            agent = team.agents[0]
            return agent.process(task)

        return self.agent_coordinator.delegate_task(task)

    def register_agent_type(self, agent_type: str, agent_class: Type) -> None:
        """Register a new agent type."""
        self.agent_factory.register_agent_type(agent_type, agent_class)

    def get_team(self, team_id: str) -> Optional[WSDETeam]:
        """Get a team by ID."""
        return self.agent_coordinator.get_team(team_id)

    def set_current_team(self, team_id: str) -> None:
        """Set the current active team."""
        self.agent_coordinator.set_current_team(team_id)
