
from typing import Any, Dict, List, Optional
from ..domain.interfaces.agent import Agent, AgentFactory, AgentCoordinator
from ..domain.models.agent import AgentConfig

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class AgentPort:
    """Port for the agent system."""
    
    def __init__(self, agent_factory: AgentFactory, agent_coordinator: AgentCoordinator):
        self.agent_factory = agent_factory
        self.agent_coordinator = agent_coordinator
    
    def create_agent(self, agent_type: str, config: Dict[str, Any] = None) -> Agent:
        """Create an agent of the specified type."""
        agent = self.agent_factory.create_agent(agent_type, config)
        self.agent_coordinator.add_agent(agent)
        return agent
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task using the appropriate agent(s)."""
        return self.agent_coordinator.delegate_task(task)
    
    def register_agent_type(self, agent_type: str, agent_class: type) -> None:
        """Register a new agent type."""
        self.agent_factory.register_agent_type(agent_type, agent_class)
