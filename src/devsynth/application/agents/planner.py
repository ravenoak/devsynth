
"""
Planner agent for the DevSynth system.
"""

from typing import Any, Dict, List
from .base import BaseAgent

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class PlannerAgent(BaseAgent):
    """Agent responsible for creating development plans."""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs and produce a development plan."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()
        
        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}
        
        You are a planning expert. Your task is to create a detailed development plan.
        
        Project context:
        {inputs.get('context', '')}
        
        Requirements:
        {inputs.get('requirements', '')}
        
        Create a detailed development plan with the following sections:
        1. Project overview
        2. Architecture design
        3. Component breakdown
        4. Implementation phases
        5. Testing strategy
        6. Deployment plan
        """
        
        # In a real implementation, this would call the LLM through a port
        # For now, we'll just return a placeholder
        plan = f"Development Plan (created by {self.name} as {self.current_role})"
        
        # Create a WSDE with the plan
        plan_wsde = self.create_wsde(
            content=plan,
            content_type="text",
            metadata={
                "agent": self.name,
                "role": self.current_role,
                "type": "development_plan"
            }
        )
        
        return {
            "plan": plan,
            "wsde": plan_wsde,
            "agent": self.name,
            "role": self.current_role
        }
    
    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "create_development_plan",
                "design_architecture",
                "define_implementation_phases",
                "create_testing_strategy",
                "create_deployment_plan"
            ]
        return capabilities
