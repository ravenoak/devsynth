"""
Context-Driven Leadership functionality for WSDE teams.

This module enhances the WSDE model with advanced context-driven leadership
capabilities, including improved expertise scoring, dynamic role switching,
and adaptive leadership selection based on task context.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
from datetime import datetime
from uuid import uuid4

from devsynth.methodology.base import Phase
from devsynth.logging_setup import DevSynthLogger

# Import the base WSDETeam class for type hints
from devsynth.domain.models.wsde_base import WSDETeam

logger = DevSynthLogger(__name__)


def enhanced_calculate_expertise_score(self: WSDETeam, agent: Any, task: Dict[str, Any]) -> float:
    """
    Calculate an enhanced expertise score for an agent based on a task.
    
    This improved scoring method provides more accurate matching between
    agent expertise and task requirements by:
    1. Considering the importance of different task aspects
    2. Weighting exact matches higher than partial matches
    3. Considering the agent's past performance in similar tasks
    4. Accounting for the agent's experience level
    
    Args:
        agent: The agent to evaluate
        task: The task to evaluate expertise for
    
    Returns:
        Expertise score (higher is better)
    """
    # Get agent expertise
    agent_expertise: List[str] = []
    
    # Try different ways to get agent expertise
    if hasattr(agent, "expertise"):
        agent_expertise = agent.expertise or []
    elif (
        hasattr(agent, "config")
        and hasattr(agent.config, "parameters")
        and "expertise" in agent.config.parameters
    ):
        agent_expertise = agent.config.parameters["expertise"] or []
    
    # If no expertise found, return 0
    if not agent_expertise:
        return 0.0
    
    # Extract keywords from the task
    task_keywords = {}
    
    # Helper function to flatten nested dictionaries for keyword extraction
    def _flatten(prefix: str, value: Any, out: Dict[str, Any]):
        if isinstance(value, dict):
            for k, v in value.items():
                _flatten(f"{prefix}.{k}" if prefix else k, v, out)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                _flatten(f"{prefix}[{i}]", v, out)
        else:
            out[prefix] = value
    
    # Flatten the task dictionary to extract all text
    flattened_task = {}
    _flatten("", task, flattened_task)
    
    # Extract all string values for keyword analysis
    for key, value in flattened_task.items():
        if isinstance(value, str):
            # Split by common separators and convert to lowercase
            words = re.split(r'[_\s\-\.]+', value.lower())
            for word in words:
                if word:  # Skip empty strings
                    # Store with the key as context for importance weighting
                    task_keywords[word] = key
    
    # Add task type as a high-importance keyword if present
    if 'type' in task and isinstance(task['type'], str):
        task_type = task['type'].lower()
        task_keywords[task_type] = 'type'
        
        # Add domain from task type if it contains an underscore
        if '_' in task_type:
            domain = task_type.split('_')[0]
            task_keywords[domain] = 'domain'
    
    # Add explicit domain as a high-importance keyword if present
    if 'domain' in task and isinstance(task['domain'], str):
        domain = task['domain'].lower()
        task_keywords[domain] = 'domain'
    
    # Calculate score based on keyword matches
    score = 0.0
    
    # Track matched expertise for logging
    matched_expertise = []
    
    for expertise in agent_expertise:
        expertise_lower = expertise.lower()
        
        # Check for matches in task keywords
        for keyword, context in task_keywords.items():
            match_score = 0.0
            
            # Exact match
            if keyword == expertise_lower:
                match_score = 2.0
                matched_expertise.append(f"{expertise} (exact match with {keyword})")
            # Keyword contains expertise
            elif expertise_lower in keyword:
                match_score = 1.0
                matched_expertise.append(f"{expertise} (contained in {keyword})")
            # Expertise contains keyword
            elif keyword in expertise_lower:
                match_score = 0.8
                matched_expertise.append(f"{expertise} (contains {keyword})")
            
            # Apply importance weighting based on context
            if match_score > 0:
                # Higher weight for type, domain, and description
                if context in ['type', 'domain']:
                    match_score *= 2.0
                elif context.endswith('description'):
                    match_score *= 1.5
                
                score += match_score
    
    # Consider agent's experience level if available
    if hasattr(agent, 'experience_level') and isinstance(agent.experience_level, (int, float)):
        experience_factor = min(1.0 + (agent.experience_level / 10.0), 2.0)
        score *= experience_factor
    
    # Consider agent's past performance if available
    if hasattr(agent, 'performance_history') and isinstance(agent.performance_history, dict):
        # Check if there's performance data for similar task types
        task_type = task.get('type', '').lower()
        if task_type in agent.performance_history:
            performance = agent.performance_history[task_type]
            # Scale between 0.8 (poor performance) and 1.2 (excellent performance)
            performance_factor = 0.8 + (performance * 0.4)
            score *= performance_factor
    
    # Log the expertise matching for debugging
    if matched_expertise:
        logger.debug(f"Agent {agent.name} expertise matches: {', '.join(matched_expertise)}")
    
    return score


def enhanced_calculate_phase_expertise_score(self: WSDETeam, agent: Any, task: Dict[str, Any], phase_keywords: List[str]) -> float:
    """
    Calculate an enhanced expertise score that considers phase-specific requirements.
    
    This improved scoring method gives higher weight to expertise that matches
    the specific requirements of the current EDRR phase, while still considering
    general task expertise.
    
    Args:
        agent: The agent to evaluate
        task: The task to evaluate expertise for
        phase_keywords: List of expertise keywords relevant for the current phase
    
    Returns:
        A score representing how well the agent's expertise matches the phase requirements
    """
    # Get the base expertise score using the enhanced method
    base_score = self.enhanced_calculate_expertise_score(agent, task)
    
    # Get agent expertise
    agent_expertise: List[str] = []
    
    # Try different ways to get agent expertise
    if hasattr(agent, "expertise"):
        agent_expertise = agent.expertise or []
    elif (
        hasattr(agent, "config")
        and hasattr(agent.config, "parameters")
        and "expertise" in agent.config.parameters
    ):
        agent_expertise = agent.config.parameters["expertise"] or []
    
    # If no expertise or phase keywords, return the base score
    if not agent_expertise or not phase_keywords:
        return base_score
    
    # Calculate phase-specific score with improved matching
    phase_score = 0.0
    
    # Track matched phase expertise for logging
    matched_phase_expertise = []
    
    for expertise in agent_expertise:
        expertise_lower = expertise.lower()
        
        for keyword in phase_keywords:
            keyword_lower = keyword.lower()
            
            # Exact match with phase keyword
            if expertise_lower == keyword_lower:
                phase_score += 3.0
                matched_phase_expertise.append(f"{expertise} (exact match with {keyword})")
            # Expertise contains phase keyword
            elif keyword_lower in expertise_lower:
                phase_score += 2.0
                matched_phase_expertise.append(f"{expertise} (contains {keyword})")
            # Phase keyword contains expertise
            elif expertise_lower in keyword_lower:
                phase_score += 1.5
                matched_phase_expertise.append(f"{expertise} (contained in {keyword})")
            # Word-level partial match
            else:
                # Split both into words and check for word-level matches
                expertise_words = expertise_lower.split('_')
                keyword_words = keyword_lower.split('_')
                
                common_words = set(expertise_words) & set(keyword_words)
                if common_words:
                    phase_score += 1.0 * len(common_words)
                    matched_phase_expertise.append(f"{expertise} (word match with {keyword}: {', '.join(common_words)})")
    
    # Log the phase expertise matching for debugging
    if matched_phase_expertise:
        logger.debug(f"Agent {agent.name} phase expertise matches: {', '.join(matched_phase_expertise)}")
    
    # Combine scores, with phase score weighted more heavily
    return base_score + (phase_score * 1.5)


def enhanced_select_primus_by_expertise(self: WSDETeam, task: Dict[str, Any]) -> Optional[Any]:
    """
    Select the Primus based on task context and agent expertise with enhanced logic.
    
    This enhanced method provides more sophisticated Primus selection by:
    1. Using improved expertise scoring
    2. Considering task domain and type more explicitly
    3. Balancing expertise with rotation to ensure all agents get leadership experience
    4. Providing detailed logging of the selection process
    
    Args:
        task: A dictionary describing the task requirements.
        
    Returns:
        The selected primus agent or None if no agents are available
    """
    if not self.agents:
        self.logger.warning("Cannot select primus: no agents in team")
        return None
    
    # Determine if we should prioritize unused agents
    unused_indices = [
        i
        for i, a in enumerate(self.agents)
        if not getattr(a, "has_been_primus", False)
    ]
    
    # If all agents have been primus, reset the flags
    if not unused_indices:
        for agent in self.agents:
            agent.has_been_primus = False
        unused_indices = list(range(len(self.agents)))
    
    # Determine the task domain and type
    task_domain = None
    task_type = task.get("type", "")
    
    # Check for domain in task
    if "domain" in task:
        task_domain = task["domain"]
    # Extract domain from task type if not explicitly specified
    elif "_" in task_type:
        task_domain = task_type.split("_")[0]
    
    # Log the task context
    self.logger.info(f"Selecting primus for task - Domain: {task_domain}, Type: {task_type}")
    
    # Calculate expertise scores for all agents
    expertise_scores = {}
    for i, agent in enumerate(self.agents):
        # Use enhanced expertise scoring
        score = self.enhanced_calculate_expertise_score(agent, task)
        
        # Apply a bonus for unused agents to encourage rotation
        if i in unused_indices:
            score *= 1.2  # 20% bonus for agents who haven't been primus
        
        expertise_scores[i] = score
        self.logger.debug(f"Agent {agent.name} expertise score: {score}")
    
    # Select the agent with the highest expertise score
    best_index = max(expertise_scores.keys(), key=lambda i: expertise_scores[i])
    best_agent = self.agents[best_index]
    
    # Update primus_index and has_been_primus flag
    self.primus_index = best_index
    best_agent.has_been_primus = True
    
    # Update roles dictionary
    self.roles["primus"] = best_agent
    
    # Log the selection
    self.logger.info(f"Selected {best_agent.name} as primus with expertise score {expertise_scores[best_index]}")
    
    # Assign roles based on the new primus
    self.assign_roles()
    
    return best_agent


def dynamic_role_reassignment_enhanced(self: WSDETeam, task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamically reassign roles based on the current task with enhanced logic.
    
    This enhanced method provides more sophisticated role assignment by:
    1. Using improved expertise scoring
    2. Considering the specific requirements of each role
    3. Ensuring appropriate role distribution based on task type
    4. Providing detailed logging of the assignment process
    
    Args:
        task: The task being worked on
    
    Returns:
        Dictionary mapping role names to assigned agents
    """
    # First, select the primus based on expertise
    self.enhanced_select_primus_by_expertise(task)
    
    # Define expertise areas for each role based on task type
    task_type = task.get("type", "").lower()
    task_domain = task.get("domain", "").lower()
    
    if not task_domain and "_" in task_type:
        task_domain = task_type.split("_")[0].lower()
    
    # Define default role expertise
    role_expertise = {
        "worker": ["implementation", "coding", "development", "execution"],
        "supervisor": ["oversight", "quality control", "review", "monitoring"],
        "designer": ["design", "architecture", "planning", "creativity"],
        "evaluator": ["testing", "evaluation", "assessment", "analysis"]
    }
    
    # Adjust role expertise based on task domain
    if task_domain == "documentation":
        role_expertise["worker"] = ["technical_writing", "documentation", "markdown"]
        role_expertise["designer"] = ["information_architecture", "documentation_structure"]
        role_expertise["evaluator"] = ["readability", "clarity", "completeness"]
    elif task_domain == "testing":
        role_expertise["worker"] = ["test_implementation", "test_writing", "test_automation"]
        role_expertise["designer"] = ["test_planning", "test_architecture", "test_strategy"]
        role_expertise["evaluator"] = ["test_evaluation", "coverage_analysis", "quality_assessment"]
    elif task_domain == "security":
        role_expertise["worker"] = ["security_implementation", "secure_coding"]
        role_expertise["designer"] = ["security_architecture", "threat_modeling"]
        role_expertise["evaluator"] = ["security_testing", "vulnerability_assessment"]
    
    # Get available agents (excluding the primus)
    available_agents = [agent for agent in self.agents if agent != self.get_primus()]
    
    # If no available agents, return current roles
    if not available_agents:
        return self.roles
    
    # Calculate role-specific expertise scores for each available agent
    role_scores = {}
    for agent in available_agents:
        role_scores[agent.name] = {}
        for role, keywords in role_expertise.items():
            score = 0.0
            if hasattr(agent, "expertise") and agent.expertise:
                for expertise in agent.expertise:
                    for keyword in keywords:
                        if keyword.lower() in expertise.lower() or expertise.lower() in keyword.lower():
                            score += 1.0
            role_scores[agent.name][role] = score
    
    # Assign roles based on expertise scores
    assigned_agents = set()
    assigned_roles = {"primus": self.get_primus()}
    
    # Assign each role to the best available agent
    for role in ["worker", "supervisor", "designer", "evaluator"]:
        # Find the best agent for this role
        best_agent = None
        best_score = -1.0
        
        for agent in available_agents:
            if agent not in assigned_agents:
                score = role_scores[agent.name][role]
                if score > best_score:
                    best_score = score
                    best_agent = agent
        
        # Assign the role if we found an agent
        if best_agent:
            assigned_roles[role] = best_agent
            assigned_agents.add(best_agent)
            self.logger.debug(f"Assigned {best_agent.name} to {role} role with score {best_score}")
    
    # If we still have unassigned roles, assign them to any remaining agents
    remaining_roles = [role for role in ["worker", "supervisor", "designer", "evaluator"] if role not in assigned_roles]
    remaining_agents = [agent for agent in available_agents if agent not in assigned_agents]
    
    for i, role in enumerate(remaining_roles):
        if i < len(remaining_agents):
            assigned_roles[role] = remaining_agents[i]
            self.logger.debug(f"Assigned {remaining_agents[i].name} to {role} role (default assignment)")
    
    # Update the roles dictionary
    for role, agent in assigned_roles.items():
        self.roles[role] = agent
        if agent:
            agent.current_role = role.capitalize()
    
    # Log the role assignments
    role_assignments = {role: agent.name if agent else None for role, agent in self.roles.items()}
    self.logger.info(f"Dynamic role assignments for task {task.get('id', 'unknown')}: {role_assignments}")
    
    return self.roles