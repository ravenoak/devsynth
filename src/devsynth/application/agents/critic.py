
"""
Critic agent for the DevSynth system.
"""

from typing import Any, Dict, List
from .base import BaseAgent

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class CriticAgent(BaseAgent):
    """Agent responsible for applying dialectical methods to critique and improve outputs."""
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs and provide critique."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()
        
        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}
        
        You are a critical thinking expert. Your task is to critique and improve outputs.
        
        Project context:
        {inputs.get('context', '')}
        
        Content to critique:
        {inputs.get('content', '')}
        
        Apply dialectical methods to critique the content:
        1. Thesis: Identify the main claims and assumptions
        2. Antithesis: Challenge these claims and assumptions
        3. Synthesis: Propose improvements that resolve the contradictions
        
        Provide a detailed critique with specific suggestions for improvement.
        """
        
        # In a real implementation, this would call the LLM through a port
        # For now, we'll just return a placeholder
        critique = f"Critique (created by {self.name} as {self.current_role})"
        
        # Create a WSDE with the critique
        critique_wsde = self.create_wsde(
            content=critique,
            content_type="text",
            metadata={
                "agent": self.name,
                "role": self.current_role,
                "type": "critique"
            }
        )
        
        return {
            "critique": critique,
            "wsde": critique_wsde,
            "agent": self.name,
            "role": self.current_role
        }
    
    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "apply_dialectical_methods",
                "identify_assumptions",
                "challenge_claims",
                "propose_improvements",
                "resolve_contradictions"
            ]
        return capabilities
