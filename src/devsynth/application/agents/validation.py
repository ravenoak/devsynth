
"""
Validation agent for the DevSynth system.
"""

from typing import Any, Dict, List
from .base import BaseAgent

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class ValidationAgent(BaseAgent):
    """Agent responsible for verifying code against tests."""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
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
        validation_report = self.generate_text(prompt)

        # Determine if the code is valid based on the report
        is_valid = "fail" not in validation_report.lower()
        
        # Create a WSDE with the validation report
        validation_wsde = self.create_wsde(
            content=validation_report,
            content_type="text",
            metadata={
                "agent": self.name,
                "role": self.current_role,
                "type": "validation_report"
            }
        )
        
        return {
            "validation_report": validation_report,
            "wsde": validation_wsde,
            "agent": self.name,
            "role": self.current_role,
            "is_valid": is_valid,
        }
    
    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "verify_code_against_tests",
                "validate_specifications",
                "check_code_quality",
                "identify_bugs",
                "suggest_improvements"
            ]
        return capabilities
