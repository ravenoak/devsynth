"""
Diagram agent for the DevSynth system.
"""

from typing import Any, Dict, List

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from .base import BaseAgent

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class DiagramAgent(BaseAgent):
    """Agent responsible for generating visual representations."""

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs and generate diagrams."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()

        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}

        You are a diagram expert. Your task is to create visual representations.

        Project context:
        {inputs.get('context', '')}

        Specifications:
        {inputs.get('specifications', '')}

        Architecture:
        {inputs.get('architecture', '')}

        Create the following diagrams:
        1. System architecture diagram
        2. Component diagram
        3. Sequence diagram
        4. Entity-relationship diagram
        5. State diagram

        Use mermaid or PlantUML syntax for the diagrams.
        """

        # Generate the diagrams using the LLM port
        diagrams = self.generate_text(prompt)

        # Create a WSDE with the diagrams
        diagram_wsde = None
        try:
            diagram_wsde = self.create_wsde(
                content=diagrams,
                content_type="diagram",
                metadata={
                    "agent": self.name,
                    "role": self.current_role,
                    "type": "diagrams",
                },
            )
        except Exception as e:
            logger.error(f"Error creating WSDE: {str(e)}")

        return {
            "diagrams": diagrams,
            "wsde": diagram_wsde,
            "agent": self.name,
            "role": self.current_role,
        }

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "create_architecture_diagrams",
                "create_component_diagrams",
                "create_sequence_diagrams",
                "create_er_diagrams",
                "create_state_diagrams",
            ]
        return capabilities
