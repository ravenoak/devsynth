"""
Critic agent for the DevSynth system.
"""

from typing import Any, Dict, List

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from .base import BaseAgent

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class CriticAgent(BaseAgent):
    """Agent responsible for applying dialectical methods to critique and improve outputs."""

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
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

        Format your response as a JSON object with the following structure:
        {{
            "thesis": {{
                "claims": ["claim1", "claim2", ...],
                "assumptions": ["assumption1", "assumption2", ...]
            }},
            "antithesis": {{
                "critique": ["critique1", "critique2", ...],
                "challenges": ["challenge1", "challenge2", ...]
            }},
            "synthesis": {{
                "improvements": ["improvement1", "improvement2", ...],
                "reasoning": "explanation of how improvements resolve contradictions"
            }}
        }}

        Provide a detailed critique with specific suggestions for improvement.
        """

        # Generate critique using the LLM port
        if self.llm_port is None:
            logger.warning("LLM port not set. Using placeholder critique.")
            critique = f"Critique (created by {self.name} as {self.current_role})"
        else:
            try:
                # Instead of using self.generate_text which logs to base.logger,
                # call the LLM port directly and log errors here
                critique = self.llm_port.generate(prompt)
                logger.info(f"Generated critique using LLM port")
            except Exception as e:
                logger.error(f"Error generating critique: {str(e)}")
                critique = f"Error generating critique: {str(e)}"

        # Create a WSDE with the critique
        critique_wsde = None
        try:
            critique_wsde = self.create_wsde(
                content=critique,
                content_type="text",
                metadata={
                    "agent": self.name,
                    "role": self.current_role,
                    "type": "critique",
                },
            )
        except Exception as e:
            logger.error(f"Error creating WSDE: {str(e)}")

        return {
            "critique": critique,
            "wsde": critique_wsde,
            "agent": self.name,
            "role": self.current_role,
        }

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "apply_dialectical_methods",
                "identify_assumptions",
                "challenge_claims",
                "propose_improvements",
                "resolve_contradictions",
            ]
        return capabilities
