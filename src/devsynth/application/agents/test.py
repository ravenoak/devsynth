"""
Test agent for the DevSynth system.
"""

from typing import Any, Dict, List
from .base import BaseAgent

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class TestAgent(BaseAgent):
    """Agent responsible for creating tests (BDD and unit tests)."""

    # Avoid pytest collecting this agent class as a test case
    __test__ = False

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs and produce tests."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()

        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}
        
        You are a testing expert. Your task is to create comprehensive tests.
        
        Project context:
        {inputs.get('context', '')}
        
        Specifications:
        {inputs.get('specifications', '')}
        
        Create comprehensive tests with the following sections:
        1. BDD feature files
        2. Unit tests
        3. Integration tests
        4. Performance tests
        5. Security tests
        """

        # In a real implementation, this would call the LLM through a port
        # For now, we'll just return a placeholder
        tests = f"Tests (created by {self.name} as {self.current_role})"

        # Create a WSDE with the tests
        test_wsde = None
        try:
            test_wsde = self.create_wsde(
                content=tests,
                content_type="text",
                metadata={
                    "agent": self.name,
                    "role": self.current_role,
                    "type": "tests",
                },
            )
        except Exception as e:
            logger.error(f"Error creating WSDE: {str(e)}")

        return {
            "tests": tests,
            "wsde": test_wsde,
            "agent": self.name,
            "role": self.current_role,
        }

    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "create_bdd_features",
                "create_unit_tests",
                "create_integration_tests",
                "create_performance_tests",
                "create_security_tests",
            ]
        return capabilities
