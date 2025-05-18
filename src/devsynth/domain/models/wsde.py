
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

@dataclass
class WSDE:
    """
    Working Structured Document Entity (WSDE) - The core knowledge unit in DevSynth.
    
    A WSDE represents a piece of structured content that can be manipulated by agents
    and stored in the memory system.
    """
    id: str = None
    content: str = ""
    content_type: str = "text"  # text, code, image, etc.
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid4())
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at

@dataclass
class WSDATeam:
    """
    Working Structured Document Agent Team (WSDA Team) - A team of agents organized
    according to the WSDE model with a rotating Primus role.
    
    The WSDE organization model consists of:
    - Worker: Performs the actual work
    - Supervisor: Oversees the work and provides guidance
    - Designer: Plans and designs the approach
    - Evaluator: Evaluates the output and provides feedback
    - Primus: The lead role that rotates among agents
    """
    agents: List[Any] = None  # List of Agent objects
    primus_index: int = 0  # Index of the current Primus agent
    
    def __post_init__(self):
        if self.agents is None:
            self.agents = []
    
    def add_agent(self, agent: Any) -> None:
        """Add an agent to the team."""
        self.agents.append(agent)
    
    def rotate_primus(self) -> None:
        """Rotate the Primus role to the next agent."""
        if self.agents:
            self.primus_index = (self.primus_index + 1) % len(self.agents)
    
    def get_primus(self) -> Optional[Any]:
        """Get the current Primus agent."""
        if not self.agents:
            return None
        return self.agents[self.primus_index]
    
    def get_worker(self) -> Optional[Any]:
        """Get the agent with the Worker role."""
        for agent in self.agents:
            if agent.current_role == "Worker":
                return agent
        return None
    
    def get_supervisor(self) -> Optional[Any]:
        """Get the agent with the Supervisor role."""
        for agent in self.agents:
            if agent.current_role == "Supervisor":
                return agent
        return None
    
    def get_designer(self) -> Optional[Any]:
        """Get the agent with the Designer role."""
        for agent in self.agents:
            if agent.current_role == "Designer":
                return agent
        return None
    
    def get_evaluator(self) -> Optional[Any]:
        """Get the agent with the Evaluator role."""
        for agent in self.agents:
            if agent.current_role == "Evaluator":
                return agent
        return None
    
    def assign_roles(self) -> None:
        """Assign WSDE roles to agents based on the current Primus."""
        if not self.agents:
            return
        
        # Roles to assign
        roles = ["Worker", "Supervisor", "Designer", "Evaluator"]
        
        # Assign Primus role to the current Primus agent
        self.agents[self.primus_index].current_role = "Primus"
        
        # Assign other roles to the remaining agents
        role_index = 0
        for i, agent in enumerate(self.agents):
            if i != self.primus_index:
                agent.current_role = roles[role_index]
                role_index = (role_index + 1) % len(roles)
