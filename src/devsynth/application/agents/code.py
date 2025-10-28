"""
Code agent for the DevSynth system.
"""

from typing import Any, Dict, List

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from .base import BaseAgent

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class CodeAgent(BaseAgent):
    """Agent responsible for implementing code based on tests."""

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs and produce code."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()

        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}

        You are a coding expert. Your task is to implement code based on tests.

        Project context:
        {inputs.get('context', '')}

        Specifications:
        {inputs.get('specifications', '')}

        Tests:
        {inputs.get('tests', '')}

        Implement code that passes the tests and meets the specifications.
        """

        # Generate the code using the LLM port
        code = self.generate_text(prompt)

        # Create a WSDE with the code
        code_wsde = None
        try:
            code_wsde = self.create_wsde(
                content=code,
                content_type="code",
                metadata={
                    "agent": self.name,
                    "role": self.current_role,
                    "type": "code",
                },
            )
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")

        return {
            "code": code,
            "wsde": code_wsde,
            "agent": self.name,
            "role": self.current_role,
        }

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "implement_code",
                "refactor_code",
                "optimize_code",
                "debug_code",
                "implement_apis",
            ]
        return capabilities
