"""
Refactor agent for the DevSynth system.
"""

from typing import Any, Dict, List

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from .base import BaseAgent

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class RefactorAgent(BaseAgent):
    """Agent responsible for improving existing code."""

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs and refactor code."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()

        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}

        You are a refactoring expert. Your task is to improve existing code.

        Project context:
        {inputs.get('context', '')}

        Code:
        {inputs.get('code', '')}

        Validation report:
        {inputs.get('validation_report', '')}

        Refactor the code to improve:
        1. Readability
        2. Maintainability
        3. Performance
        4. Security
        5. Testability

        Provide a detailed explanation of the changes made.
        """

        # Generate the refactored code and explanation using the LLM port
        refactored_code = self.generate_text(prompt)
        refactor_explanation = self.generate_text(
            f"{prompt}\nProvide an explanation of the refactoring decisions."
        )

        # Create WSDEs with the refactored code and explanation
        code_wsde = None
        explanation_wsde = None

        # Try to create the code WSDE, but handle any exceptions
        try:
            code_wsde = self.create_wsde(
                content=refactored_code,
                content_type="code",
                metadata={
                    "agent": self.name,
                    "role": self.current_role,
                    "type": "refactored_code",
                },
            )
        except Exception as e:
            logger.error(f"Error creating code WSDE: {str(e)}")

        # Try to create the explanation WSDE, but handle any exceptions
        try:
            explanation_wsde = self.create_wsde(
                content=refactor_explanation,
                content_type="text",
                metadata={
                    "agent": self.name,
                    "role": self.current_role,
                    "type": "refactor_explanation",
                },
            )
        except Exception as e:
            logger.error(f"Error creating explanation WSDE: {str(e)}")

        return {
            "refactored_code": refactored_code,
            "explanation": refactor_explanation,
            "code_wsde": code_wsde,
            "explanation_wsde": explanation_wsde,
            "agent": self.name,
            "role": self.current_role,
        }

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "refactor_code",
                "improve_readability",
                "improve_maintainability",
                "optimize_performance",
                "enhance_security",
                "improve_testability",
            ]
        return capabilities
