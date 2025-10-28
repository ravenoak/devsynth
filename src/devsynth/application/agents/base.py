"""
Base agent class for the DevSynth system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.agent import Agent
from ...domain.models.agent import AgentConfig
from ...domain.models.wsde import WSDE
from ...ports.llm_port import LLMPort

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class BaseAgent(Agent, ABC):
    """Base class for all agents in the DevSynth system."""

    def __init__(self):
        self.config = None
        self.current_role = (
            None  # Current WSDE role (Worker, Supervisor, Designer, Evaluator, Primus)
        )
        self.llm_port = None

    def initialize(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration."""
        self.config = config

    def set_llm_port(self, llm_port: LLMPort) -> None:
        """Set the LLM port for this agent."""
        self.llm_port = llm_port

    def generate_text(self, prompt: str, parameters: dict[str, Any] = None) -> str:
        """Generate text using the LLM port."""
        if self.llm_port is None:
            logger.warning("LLM port not set. Using placeholder text.")
            return f"Placeholder text for prompt: {prompt[:30]}..."

        try:
            return self.llm_port.generate(prompt, parameters)
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return f"Error generating text: {str(e)}"

    def generate_text_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] = None,
    ) -> str:
        """Generate text with conversation context using the LLM port."""
        if self.llm_port is None:
            logger.warning("LLM port not set. Using placeholder text.")
            return f"Placeholder text for prompt with context: {prompt[:30]}..."

        try:
            return self.llm_port.generate_with_context(prompt, context, parameters)
        except Exception as e:
            logger.error(f"Error generating text with context: {str(e)}")
            return f"Error generating text with context: {str(e)}"

    @abstractmethod
    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs and produce outputs."""
        pass

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent."""
        if self.config:
            return self.config.capabilities
        return []

    @property
    def name(self) -> str:
        """Get the name of this agent."""
        if self.config:
            return self.config.name
        return self.__class__.__name__

    @name.setter
    def name(self, value: str) -> None:
        """Set the agent name, updating :class:`AgentConfig` if necessary."""
        if self.config:
            self.config.name = value
        else:  # pragma: no cover - defensive
            self.config = AgentConfig(name=value)

    @property
    def agent_type(self) -> str:
        """Get the type of this agent."""
        if self.config:
            return self.config.agent_type.value
        return "base"

    @property
    def description(self) -> str:
        """Get the description of this agent."""
        if self.config:
            return self.config.description
        return "Base agent"

    def create_wsde(
        self, content: str, content_type: str = "text", metadata: dict[str, Any] = None
    ) -> WSDE:
        """Create a new WSDE with the given content."""
        return WSDE(content=content, content_type=content_type, metadata=metadata or {})

    def update_wsde(
        self, wsde: WSDE, content: str = None, metadata: dict[str, Any] = None
    ) -> WSDE:
        """Update an existing WSDE."""
        if content is not None:
            wsde.content = content

        if metadata:
            wsde.metadata.update(metadata)

        return wsde

    def get_role_prompt(self) -> str:
        """Get a prompt based on the current WSDE role."""
        if self.current_role == "Worker":
            return "As the Worker, your job is to perform the actual work and implement the solution."
        elif self.current_role == "Supervisor":
            return "As the Supervisor, your job is to oversee the work and provide guidance and direction."
        elif self.current_role == "Designer":
            return "As the Designer, your job is to plan and design the approach and architecture."
        elif self.current_role == "Evaluator":
            return "As the Evaluator, your job is to evaluate the output and provide feedback for improvement."
        elif self.current_role == "Primus":
            return "As the Primus, you are the lead for this task. Coordinate the team and make final decisions."
        else:
            return ""
