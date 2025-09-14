from __future__ import annotations

from abc import abstractmethod
from typing import Any, Protocol

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...domain.models.agent import AgentConfig

logger = DevSynthLogger(__name__)


class Agent(Protocol):
    """Protocol for agents in the DevSynth system."""

    @abstractmethod
    def initialize(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration."""
        ...

    @abstractmethod
    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs and produce outputs."""
        ...

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent."""
        ...


class AgentFactory(Protocol):
    """Protocol for creating agents."""

    @abstractmethod
    def create_agent(
        self, agent_type: str, config: dict[str, Any] | None = None
    ) -> Agent:
        """Create an agent of the specified type."""
        ...

    @abstractmethod
    def register_agent_type(self, agent_type: str, agent_class: type) -> None:
        """Register a new agent type."""
        ...


class AgentCoordinator(Protocol):
    """Protocol for coordinating multiple agents."""

    @abstractmethod
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the coordinator."""
        ...

    @abstractmethod
    def delegate_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Delegate a task to the appropriate agent(s)."""
        ...
