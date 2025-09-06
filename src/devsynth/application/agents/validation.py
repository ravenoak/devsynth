"""
Validation agent for the DevSynth system.
"""

from typing import Any, Dict, List, TypedDict, cast
from collections.abc import Mapping, MutableMapping

from devsynth.logging_setup import DevSynthLogger

from .base import BaseAgent

logger = DevSynthLogger(__name__)


class ValidationAgent(BaseAgent):
    """Agent responsible for verifying code against tests."""

    class ProcessOutput(TypedDict):
        validation_report: str
        wsde: Any
        agent: str
        role: str
        is_valid: bool

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs and validate code against tests."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()

        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}

        You are a validation expert. Your task is to verify code against tests.

        Project context:
        {inputs.get('context', '')}

        Specifications:
        {inputs.get('specifications', '')}

        Tests:
        {inputs.get('tests', '')}

        Code:
        {inputs.get('code', '')}

        Verify that the code passes the tests and meets the specifications.
        Provide a detailed validation report.
        """

        # Generate the validation report using the LLM port
        validation_report = str(self.generate_text(prompt))

        # Determine if the code is valid based on the report
        lowered = validation_report.lower()
        # Consider only whole-word occurrences of fail/error/exception to avoid false positives like "failures"
        import re

        is_valid = re.search(r"\b(fail|error|exception)\b", lowered) is None

        # Create a WSDE with the validation report
        validation_wsde = self.create_wsde(
            content=validation_report,
            content_type="text",
            metadata={
                "agent": self.name,
                "role": self.current_role,
                "type": "validation_report",
            },
        )

        out: ValidationAgent.ProcessOutput = {
            "validation_report": validation_report,
            "wsde": validation_wsde,
            "agent": self.name,
            "role": str(self.current_role or "validator"),
            "is_valid": is_valid,
        }
        return cast(dict[str, Any], out)

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent.

        Returns a default list if the base class returns an empty list or None.
        """
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "verify_code_against_tests",
                "validate_specifications",
                "check_code_quality",
                "identify_bugs",
                "suggest_improvements",
            ]
        return capabilities
