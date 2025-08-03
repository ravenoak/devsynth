"""
EDRR Templates Module.

This module defines the templates used by the EDRR framework for each phase.
It provides functions to register these templates with the PromptManager.
"""

from typing import Dict, Any, Optional

from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.methodology.base import Phase
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Define templates for each EDRR phase
EXPAND_PHASE_TEMPLATE = """
# Expand Phase for Task: {task_description}

## Objective
Generate diverse ideas, explore broadly, and gather relevant knowledge for the task.

## Instructions
1. Consider multiple approaches to the problem
2. Explore different perspectives and angles
3. Generate a wide range of potential solutions
4. Identify relevant knowledge and resources
5. Don't evaluate or filter ideas yet - focus on quantity and diversity

## Task Context
{task_description}

## Questions to Consider
- What are all the possible ways to approach this task?
- What similar problems have been solved before?
- What knowledge domains are relevant to this task?
- What creative or unconventional approaches might work?
- What are the key components or sub-problems within this task?
"""

DIFFERENTIATE_PHASE_TEMPLATE = """
# Differentiate Phase for Task: {task_description}

## Objective
Analyze and compare the ideas generated in the Expand phase, evaluate options, and identify trade-offs.

## Instructions
1. Compare and contrast different approaches
2. Evaluate each option against relevant criteria
3. Identify strengths and weaknesses of each approach
4. Analyze trade-offs between different solutions
5. Develop decision criteria for selecting the best approach

## Task Context
{task_description}

## Questions to Consider
- What are the key differences between the approaches?
- What criteria are most important for evaluating solutions?
- What are the trade-offs between different approaches?
- Which approaches best align with the requirements?
- What are the risks and benefits of each approach?
"""

REFINE_PHASE_TEMPLATE = """
# Refine Phase for Task: {task_description}

## Objective
Elaborate on the selected approach, develop a detailed implementation plan, and optimize the solution.

## Instructions
1. Develop a detailed plan for the selected approach
2. Elaborate on implementation details
3. Optimize the solution for performance, maintainability, and other relevant factors
4. Identify potential issues and develop mitigation strategies
5. Create quality assurance checks for the implementation

## Task Context
{task_description}

## Questions to Consider
- What are the specific steps needed to implement this solution?
- How can the solution be optimized?
- What edge cases need to be handled?
- What quality checks should be performed?
- How can the implementation be made more robust?
"""

RETROSPECT_PHASE_TEMPLATE = """
# Retrospect Phase for Task: {task_description}

## Objective
Extract learnings, identify patterns, integrate knowledge, and generate improvement suggestions.

## Instructions
1. Reflect on the entire process from Expand through Refine
2. Extract key learnings and insights
3. Identify patterns that could be applied to future tasks
4. Integrate new knowledge into the existing knowledge base
5. Generate suggestions for improving the process and solution

## Task Context
{task_description}

## Questions to Consider
- What worked well in this process?
- What challenges were encountered and how were they addressed?
- What patterns or principles emerged that could be reused?
- How could the process be improved for similar tasks in the future?
- What new knowledge was gained that should be preserved?
"""

def register_edrr_templates(prompt_manager: PromptManager) -> None:
    """
    Register all EDRR phase templates with the prompt manager.
    
    Args:
        prompt_manager: The prompt manager to register templates with
    """
    try:
        # Register Expand phase template
        prompt_manager.register_template(
            name="expand_phase",
            description="Template for the Expand phase of the EDRR cycle",
            template_text=EXPAND_PHASE_TEMPLATE,
            edrr_phase="EXPAND"
        )
        logger.info("Registered expand_phase template")
        
        # Register Differentiate phase template
        prompt_manager.register_template(
            name="differentiate_phase",
            description="Template for the Differentiate phase of the EDRR cycle",
            template_text=DIFFERENTIATE_PHASE_TEMPLATE,
            edrr_phase="DIFFERENTIATE"
        )
        logger.info("Registered differentiate_phase template")
        
        # Register Refine phase template
        prompt_manager.register_template(
            name="refine_phase",
            description="Template for the Refine phase of the EDRR cycle",
            template_text=REFINE_PHASE_TEMPLATE,
            edrr_phase="REFINE"
        )
        logger.info("Registered refine_phase template")
        
        # Register Retrospect phase template
        prompt_manager.register_template(
            name="retrospect_phase",
            description="Template for the Retrospect phase of the EDRR cycle",
            template_text=RETROSPECT_PHASE_TEMPLATE,
            edrr_phase="RETROSPECT"
        )
        logger.info("Registered retrospect_phase template")
        
    except ValueError as e:
        # This might happen if templates are already registered
        logger.warning(f"Error registering EDRR templates: {str(e)}")