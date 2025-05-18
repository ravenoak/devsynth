"""
Agent adapter for the DevSynth system.
Implements the AgentFactory and AgentCoordinator interfaces.

This implementation focuses on the single-agent design for MVP while
preserving extension points for future multi-agent capabilities.
"""

from typing import Any, Dict, List, Optional, Type
from ...domain.interfaces.agent import Agent, AgentFactory, AgentCoordinator
from ...domain.models.agent import AgentConfig, AgentType
from ...domain.models.wsde import WSDATeam
from ...application.agents.unified_agent import UnifiedAgent
from ...ports.llm_port import LLMPort

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

# Import legacy agent classes (commented out for MVP but retained for future reference)
# from ...application.agents.base import BaseAgent
# from ...application.agents.planner import PlannerAgent
# from ...application.agents.specification import SpecificationAgent
# from ...application.agents.test import TestAgent
# from ...application.agents.code import CodeAgent
# from ...application.agents.validation import ValidationAgent
# from ...application.agents.refactor import RefactorAgent
# from ...application.agents.documentation import DocumentationAgent
# from ...application.agents.diagram import DiagramAgent
# from ...application.agents.critic import CriticAgent

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
        }
        self.llm_port = llm_port

        # Extension point: This dictionary can be expanded in future versions
        # to support multiple specialized agents
        self.future_agent_types = {
            # Commented out for MVP but retained for future reference
            # AgentType.PLANNER.value: PlannerAgent,
            # AgentType.SPECIFICATION.value: SpecificationAgent,
            # AgentType.TEST.value: TestAgent,
            # AgentType.CODE.value: CodeAgent,
            # AgentType.VALIDATION.value: ValidationAgent,
            # AgentType.REFACTOR.value: RefactorAgent,
            # AgentType.DOCUMENTATION.value: DocumentationAgent,
            # AgentType.DIAGRAM.value: DiagramAgent,
            # AgentType.CRITIC.value: CriticAgent,
        }

    def create_agent(self, agent_type: str, config: Dict[str, Any] = None) -> Agent:
        """
        Create an agent of the specified type.

        For MVP, this always returns a UnifiedAgent regardless of the requested type,
        ensuring backward compatibility with existing code.
        """
        # For MVP, always use the UnifiedAgent
        agent_class = UnifiedAgent

        # Extension point: In future versions, this can be expanded to use
        # different agent classes based on the agent_type
        agent = agent_class()

        if config:
            # Use the requested agent_type for backward compatibility
            agent_config = AgentConfig(
                name=config.get("name", f"{agent_type}_agent"),
                agent_type=AgentType(agent_type) if agent_type in [e.value for e in AgentType] else AgentType.ORCHESTRATOR,
                description=config.get("description", f"Agent for {agent_type} tasks"),
                capabilities=config.get("capabilities", []),
                parameters=config.get("parameters", {})
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
        # For MVP, this is a no-op
        # In future versions, this will register new agent types
        pass

class WSDATeamCoordinator(AgentCoordinator):
    """
    Coordinator for WSDA teams.

    This class is retained for future multi-agent capabilities but is simplified
    for MVP to work with a single agent.
    """

    def __init__(self):
        self.teams = {}  # Dictionary of teams by team_id
        self.current_team_id = None

    def create_team(self, team_id: str) -> WSDATeam:
        """Create a new WSDA team."""
        team = WSDATeam()
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

    def delegate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate a task to the appropriate agent(s) in the current team.

        For MVP, this simply passes the task to the single agent.
        """
        if self.current_team_id is None:
            raise ValidationError(f"No active team. Create a team first.")

        team = self.teams[self.current_team_id]

        # For MVP, we only have one agent
        if len(team.agents) == 0:
            raise ValidationError(f"No agents in the team.")

        # For MVP, just use the first agent
        agent = team.agents[0]

        # Process the task
        return agent.process(task)

    def get_team(self, team_id: str) -> Optional[WSDATeam]:
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

    def __init__(self, llm_port: Optional[LLMPort] = None):
        self.agent_factory = SimplifiedAgentFactory(llm_port)
        self.agent_coordinator = WSDATeamCoordinator()
        self.llm_port = llm_port

    def create_agent(self, agent_type: str, config: Dict[str, Any] = None) -> Agent:
        """Create an agent of the specified type."""
        return self.agent_factory.create_agent(agent_type, config)

    def create_team(self, team_id: str) -> WSDATeam:
        """Create a new WSDA team."""
        return self.agent_coordinator.create_team(team_id)

    def add_agent_to_team(self, agent: Agent) -> None:
        """Add an agent to the current team."""
        self.agent_coordinator.add_agent(agent)

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task using the current team."""
        return self.agent_coordinator.delegate_task(task)

    def register_agent_type(self, agent_type: str, agent_class: Type) -> None:
        """Register a new agent type."""
        self.agent_factory.register_agent_type(agent_type, agent_class)

    def get_team(self, team_id: str) -> Optional[WSDATeam]:
        """Get a team by ID."""
        return self.agent_coordinator.get_team(team_id)

    def set_current_team(self, team_id: str) -> None:
        """Set the current active team."""
        self.agent_coordinator.set_current_team(team_id)
