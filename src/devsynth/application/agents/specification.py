
"""
Specification agent for the DevSynth system.
"""

from typing import Any, Dict, List
from .base import BaseAgent

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class SpecificationAgent(BaseAgent):
    """Agent responsible for generating specifications."""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs and produce specifications."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()
        
        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}
        
        You are a specification expert. Your task is to create detailed specifications.
        
        Project context:
        {inputs.get('context', '')}
        
        Requirements:
        {inputs.get('requirements', '')}
        
        Development plan:
        {inputs.get('plan', '')}
        
        Create detailed specifications with the following sections:
        1. Functional requirements
        2. Non-functional requirements
        3. API specifications
        4. Data models
        5. User interfaces
        6. Integration points
        """
        
        # In a real implementation, this would call the LLM through a port
        # For now, we'll just return a placeholder
        specifications = f"Specifications (created by {self.name} as {self.current_role})"
        
        # Create a WSDE with the specifications
        spec_wsde = self.create_wsde(
            content=specifications,
            content_type="text",
            metadata={
                "agent": self.name,
                "role": self.current_role,
                "type": "specifications"
            }
        )
        
        return {
            "specifications": specifications,
            "wsde": spec_wsde,
            "agent": self.name,
            "role": self.current_role
        }
    
    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "create_functional_requirements",
                "create_non_functional_requirements",
                "define_api_specifications",
                "define_data_models",
                "design_user_interfaces",
                "identify_integration_points"
            ]
        return capabilities
