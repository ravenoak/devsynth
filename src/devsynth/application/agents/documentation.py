"""
Documentation agent for the DevSynth system.
"""

from typing import Any, Dict, List

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from .base import BaseAgent

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class DocumentationAgent(BaseAgent):
    """Agent responsible for creating documentation."""

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs and create documentation."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()

        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}

        You are a documentation expert. Your task is to create comprehensive documentation.

        Project context:
        {inputs.get('context', '')}

        Specifications:
        {inputs.get('specifications', '')}

        Code:
        {inputs.get('code', '')}

        Create comprehensive documentation with the following sections:
        1. Overview
        2. Installation
        3. Usage
        4. API reference
        5. Examples
        6. Troubleshooting
        """

        # Generate the documentation using the LLM port
        documentation = self.generate_text(prompt)

        # Create a WSDE with the documentation
        doc_wsde = None
        try:
            doc_wsde = self.create_wsde(
                content=documentation,
                content_type="text",
                metadata={
                    "agent": self.name,
                    "role": self.current_role,
                    "type": "documentation",
                },
            )
        except Exception as e:
            logger.error(f"Error creating WSDE: {str(e)}")

        return {
            "documentation": documentation,
            "wsde": doc_wsde,
            "agent": self.name,
            "role": self.current_role,
        }

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "create_user_documentation",
                "create_api_documentation",
                "create_installation_guides",
                "create_usage_examples",
                "create_troubleshooting_guides",
            ]
        return capabilities
