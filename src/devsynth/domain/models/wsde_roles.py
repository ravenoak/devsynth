"""
WSDE role management and expertise calculation functionality.

This module contains functionality for managing roles in a WSDE team,
including role assignment, expertise calculation, and role rotation.
"""

from typing import Any, Dict, List, Optional
from devsynth.methodology.base import Phase
from devsynth.logging_setup import DevSynthLogger

# Import the base WSDETeam class for type hints
from devsynth.domain.models.wsde_base import WSDETeam

logger = DevSynthLogger(__name__)


def assign_roles(self: WSDETeam, role_mapping: Optional[Dict[str, Any]] = None):
    """
    Assign roles to agents in the team.

    Args:
        role_mapping: Optional dictionary mapping role names to agents
                     If not provided, roles will be auto-assigned

    Returns:
        Dictionary mapping role names to assigned agents
    """
    if role_mapping:
        self._validate_role_mapping(role_mapping)
        for role, agent in role_mapping.items():
            self.roles[role] = agent
    else:
        self._auto_assign_roles()

    # Log the role assignments
    role_assignments = {
        role: getattr(agent, "name", getattr(agent, "id", None)) if agent else None
        for role, agent in self.roles.items()
    }
    self.logger.info(f"Role assignments for team {self.name}: {role_assignments}")

    return self.roles


def assign_roles_for_phase(self: WSDETeam, phase: Phase, task: Dict[str, Any]):
    """
    Assign roles based on the current EDRR phase.

    This method assigns roles based on the specific requirements of each
    phase in the EDRR (Expand, Differentiate, Refine, Reflect) cycle.

    Args:
        phase: The current EDRR phase
        task: The task being worked on

    Returns:
        Dictionary mapping role names to assigned agents
    """
    self.logger.info(f"Assigning roles for phase {phase.name} in team {self.name}")

    # Use the phase-specific role assignment method
    return self._assign_roles_for_edrr_phase(phase, task)


def _assign_roles_for_edrr_phase(self: WSDETeam, phase: Phase, task: Dict[str, Any]):
    """
    Internal method to assign roles based on EDRR phase.

    Args:
        phase: The current EDRR phase
        task: The task being worked on

    Returns:
        Dictionary mapping role names to assigned agents
    """
    # Reset all roles
    for role in self.roles:
        self.roles[role] = None

    if not self.agents:
        self.logger.warning(
            f"Cannot assign roles for phase {phase.name}: no agents in team"
        )
        return self.roles

    # Define phase-specific expertise keywords
    phase_expertise = {
        "expand": [
            "exploration",
            "brainstorming",
            "divergent thinking",
            "idea generation",
            "research",
            "information gathering",
            "discovery",
            "exploration",
            "creativity",
            "innovation",
            "possibilities",
            "alternatives",
        ],
        "differentiate": [
            "analysis",
            "comparison",
            "categorization",
            "classification",
            "distinction",
            "differentiation",
            "evaluation",
            "assessment",
            "critical thinking",
            "discernment",
            "judgment",
            "discrimination",
        ],
        "refine": [
            "refinement",
            "improvement",
            "enhancement",
            "optimization",
            "polishing",
            "editing",
            "revision",
            "iteration",
            "detail-oriented",
            "precision",
            "accuracy",
            "quality control",
            "fine-tuning",
        ],
        "reflect": [
            "reflection",
            "retrospective",
            "review",
            "evaluation",
            "assessment",
            "learning",
            "insight",
            "understanding",
            "metacognition",
            "self-awareness",
            "introspection",
            "contemplation",
        ],
    }

    # Get the phase name in lowercase
    phase_name = phase.name.lower()

    # Get the relevant expertise keywords for this phase
    keywords = phase_expertise.get(phase_name, [])

    # Calculate expertise scores for each agent based on the phase
    expertise_scores = {}
    for agent in self.agents:
        expertise_scores[agent.name] = self._calculate_phase_expertise_score(
            agent, task, keywords
        )

    # Sort agents by expertise score (descending)
    sorted_agents = sorted(
        self.agents, key=lambda a: expertise_scores[a.name], reverse=True
    )

    # Assign roles based on expertise scores and phase requirements
    if phase_name == "expand":
        # In Expand phase, the most creative agent should be Primus
        if sorted_agents:
            self.roles["primus"] = sorted_agents[0]
            self.roles["worker"] = sorted_agents[min(1, len(sorted_agents) - 1)]
            self.roles["designer"] = sorted_agents[min(2, len(sorted_agents) - 1)]
            self.roles["supervisor"] = sorted_agents[min(3, len(sorted_agents) - 1)]
            self.roles["evaluator"] = sorted_agents[min(4, len(sorted_agents) - 1)]

    elif phase_name == "differentiate":
        # In Differentiate phase, the most analytical agent should be Primus
        if sorted_agents:
            self.roles["primus"] = sorted_agents[0]
            self.roles["evaluator"] = sorted_agents[min(1, len(sorted_agents) - 1)]
            self.roles["supervisor"] = sorted_agents[min(2, len(sorted_agents) - 1)]
            self.roles["worker"] = sorted_agents[min(3, len(sorted_agents) - 1)]
            self.roles["designer"] = sorted_agents[min(4, len(sorted_agents) - 1)]

    elif phase_name == "refine":
        # In Refine phase, the most detail-oriented agent should be Primus
        if sorted_agents:
            self.roles["primus"] = sorted_agents[0]
            self.roles["worker"] = sorted_agents[min(1, len(sorted_agents) - 1)]
            self.roles["designer"] = sorted_agents[min(2, len(sorted_agents) - 1)]
            self.roles["evaluator"] = sorted_agents[min(3, len(sorted_agents) - 1)]
            self.roles["supervisor"] = sorted_agents[min(4, len(sorted_agents) - 1)]

    elif phase_name == "reflect":
        # In Reflect phase, the most reflective agent should be Primus
        if sorted_agents:
            self.roles["primus"] = sorted_agents[0]
            self.roles["evaluator"] = sorted_agents[min(1, len(sorted_agents) - 1)]
            self.roles["supervisor"] = sorted_agents[min(2, len(sorted_agents) - 1)]
            self.roles["designer"] = sorted_agents[min(3, len(sorted_agents) - 1)]
            self.roles["worker"] = sorted_agents[min(4, len(sorted_agents) - 1)]

    # Log the role assignments
    role_assignments = {
        role: agent.name if agent else None for role, agent in self.roles.items()
    }
    self.logger.info(f"Role assignments for phase {phase.name}: {role_assignments}")

    return self.roles


def _validate_role_mapping(self: WSDETeam, mapping: Dict[str, Any]):
    """
    Validate a role mapping dictionary.

    Args:
        mapping: Dictionary mapping role names to agents

    Raises:
        ValueError: If the mapping contains invalid roles or agents
    """
    valid_roles = set(self.roles.keys())
    for role, agent in mapping.items():
        if role not in valid_roles:
            raise ValueError(
                f"Invalid role: {role}. Valid roles are: {', '.join(valid_roles)}"
            )
        if agent is not None and agent not in self.agents:
            raise ValueError(f"Agent {agent.name} is not a member of this team")


def _auto_assign_roles(self: WSDETeam):
    """
    Automatically assign roles based on agent expertise.

    This method assigns roles based on the expertise of each agent,
    ensuring that each role is filled by an agent with appropriate skills.
    """
    if not self.agents:
        self.logger.warning("Cannot auto-assign roles: no agents in team")
        return

    # Reset all roles
    for role in self.roles:
        self.roles[role] = None

    # Define expertise areas for each role
    role_expertise = {
        "primus": [
            "leadership",
            "coordination",
            "decision-making",
            "strategic thinking",
        ],
        "worker": ["implementation", "coding", "development", "execution"],
        "supervisor": ["oversight", "quality control", "review", "monitoring"],
        "designer": ["design", "architecture", "planning", "creativity"],
        "evaluator": ["testing", "evaluation", "assessment", "analysis"],
    }

    # Function to calculate expertise score for an agent
    def get_expertise(agent: Any):
        expertise_scores = {}
        for role, keywords in role_expertise.items():
            score = 0
            # Check agent's expertise against role keywords
            if hasattr(agent, "expertise") and isinstance(agent.expertise, list):
                for keyword in keywords:
                    if any(keyword.lower() in exp.lower() for exp in agent.expertise):
                        score += 1
            expertise_scores[role] = score
        return expertise_scores

    # Calculate expertise scores for all agents
    agent_expertise = {agent: get_expertise(agent) for agent in self.agents}

    # Assign roles based on expertise scores
    assigned_agents = set()

    # First, assign the primus role to the agent with highest primus expertise
    primus_candidates = sorted(
        self.agents, key=lambda a: agent_expertise[a]["primus"], reverse=True
    )
    if primus_candidates:
        self.roles["primus"] = primus_candidates[0]
        assigned_agents.add(primus_candidates[0])

    # Then assign other roles to remaining agents based on expertise
    for role in ["worker", "supervisor", "designer", "evaluator"]:
        candidates = sorted(
            [a for a in self.agents if a not in assigned_agents],
            key=lambda a: agent_expertise[a][role],
            reverse=True,
        )
        if candidates:
            self.roles[role] = candidates[0]
            assigned_agents.add(candidates[0])

    # Log the role assignments
    role_assignments = {
        role: agent.name if agent else None for role, agent in self.roles.items()
    }
    self.logger.info(f"Auto-assigned roles for team {self.name}: {role_assignments}")


def get_role_map(self: WSDETeam):
    """
    Get a mapping of agent names to roles.

    Returns:
        Dictionary mapping agent names to role names
    """
    # First create a mapping of roles to agent names (original behavior)
    role_to_agent = {
        role: agent.name if agent else None for role, agent in self.roles.items()
    }

    # Then invert the mapping to get agent names to roles
    agent_to_role = {}
    for role, agent_name in role_to_agent.items():
        if agent_name is not None:
            agent_to_role[agent_name] = role.capitalize()

    return agent_to_role


def dynamic_role_reassignment(self: WSDETeam, task: Dict[str, Any]):
    """
    Dynamically reassign roles based on the current task.

    This method uses expertise scoring to reassign roles based on the
    specific requirements of the current task.

    Args:
        task: The task being worked on

    Returns:
        Dictionary mapping role names to assigned agents
    """
    best_agent = self.select_primus_by_expertise(task)

    # Update primus_index to keep get_primus in sync with new role
    if best_agent in self.agents:
        self.primus_index = self.agents.index(best_agent)
        setattr(best_agent, "has_been_primus", True)

    # Determine the EDRR phase for role assignment
    phase_value = task.get("phase", "expand")
    if isinstance(phase_value, Phase):
        phase = phase_value
    else:
        try:
            phase = Phase(phase_value)
        except Exception:
            phase = Phase.EXPAND

    # Assign roles for the detected phase
    self.assign_roles_for_phase(phase, task)

    return self.roles


def _calculate_expertise_score(self: WSDETeam, agent: Any, task: Dict[str, Any]):
    """
    Calculate an expertise score for an agent based on a task.

    Args:
        agent: The agent to evaluate
        task: The task to evaluate expertise for

    Returns:
        Expertise score (higher is better)
    """
    if not hasattr(agent, "expertise") or not agent.expertise:
        return 0

    # Extract keywords from the task
    task_keywords = []

    # Extract from task description
    if "description" in task and task["description"]:
        task_keywords.extend(task["description"].lower().split())

    # Extract from task requirements
    if "requirements" in task and task["requirements"]:
        if isinstance(task["requirements"], list):
            for req in task["requirements"]:
                if isinstance(req, str):
                    task_keywords.extend(req.lower().split())
                elif isinstance(req, dict) and "description" in req:
                    task_keywords.extend(req["description"].lower().split())
        elif isinstance(task["requirements"], str):
            task_keywords.extend(task["requirements"].lower().split())

    # Calculate score based on keyword matches
    score = 0
    for expertise in agent.expertise:
        expertise_lower = expertise.lower()
        for keyword in task_keywords:
            if keyword in expertise_lower or expertise_lower in keyword:
                score += 1

    return score


def _calculate_phase_expertise_score(
    self: WSDETeam, agent: Any, task: Dict[str, Any], phase_keywords: List[str]
):
    """
    Calculate an expertise score for an agent based on a task and phase keywords.

    Args:
        agent: The agent to evaluate
        task: The task to evaluate expertise for
        phase_keywords: List of keywords relevant to the current phase

    Returns:
        Expertise score (higher is better)
    """
    if not hasattr(agent, "expertise") or not agent.expertise:
        return 0

    # Extract keywords from the task
    task_keywords = []

    # Extract from task description
    if "description" in task and task["description"]:
        task_keywords.extend(task["description"].lower().split())

    # Extract from task requirements
    if "requirements" in task and task["requirements"]:
        if isinstance(task["requirements"], list):
            for req in task["requirements"]:
                if isinstance(req, str):
                    task_keywords.extend(req.lower().split())
                elif isinstance(req, dict) and "description" in req:
                    task_keywords.extend(req["description"].lower().split())
        elif isinstance(task["requirements"], str):
            task_keywords.extend(task["requirements"].lower().split())

    # Calculate score based on keyword matches
    base_score = 0
    for expertise in agent.expertise:
        expertise_lower = expertise.lower()
        for keyword in task_keywords:
            if keyword in expertise_lower or expertise_lower in keyword:
                base_score += 1

    # Calculate phase-specific score
    phase_score = 0
    for expertise in agent.expertise:
        expertise_lower = expertise.lower()
        for keyword in phase_keywords:
            if keyword in expertise_lower or expertise_lower in keyword:
                phase_score += 2  # Phase-specific expertise is weighted more heavily

    # Combine scores, with phase score weighted more heavily
    return base_score + (phase_score * 2)


def select_primus_by_expertise(self: WSDETeam, task: Dict[str, Any]):
    """
    Select a primus based on expertise for the given task.

    Args:
        task: The task to select a primus for

    Returns:
        The selected primus agent or None if no agents are available
    """
    if not self.agents:
        self.logger.warning("Cannot select primus: no agents in team")
        return None

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
    task_text = " ".join(
        str(v) for v in flattened_task.values() if isinstance(v, (str, int, float))
    )

    # Calculate expertise scores for each agent
    expertise_scores = {}
    for agent in self.agents:
        if hasattr(agent, "expertise"):
            score = 0
            for expertise in agent.expertise:
                if expertise.lower() in task_text.lower():
                    score += 1
            expertise_scores[agent.name] = score
        else:
            expertise_scores[agent.name] = 0

    # Select the agent with the highest expertise score
    best_agent = max(self.agents, key=lambda a: expertise_scores[a.name])

    # Assign the selected agent as primus
    self.roles["primus"] = best_agent
    self.logger.info(
        f"Selected {best_agent.name} as primus based on expertise for task"
    )

    return best_agent


def rotate_roles(self: WSDETeam):
    """
    Rotate all roles among team members.

    This method rotates all roles to different agents, ensuring that
    each agent gets a chance to perform different roles.

    Returns:
        Dictionary mapping role names to assigned agents
    """
    if len(self.agents) < 2:
        self.logger.warning("Cannot rotate roles: need at least 2 agents")
        return self.roles

    # Get current role assignments
    current_roles = {
        role: agent for role, agent in self.roles.items() if agent is not None
    }

    # If no roles are assigned, assign them first
    if not current_roles:
        self._auto_assign_roles()
        return self.roles

    # Create a list of agents in role order
    role_order = ["primus", "worker", "supervisor", "designer", "evaluator"]
    agents_in_order = [
        self.roles[role] for role in role_order if self.roles[role] is not None
    ]

    # Add any agents not currently assigned a role
    unassigned_agents = [agent for agent in self.agents if agent not in agents_in_order]
    agents_in_order.extend(unassigned_agents)

    # Rotate agents (shift right)
    if agents_in_order:
        rotated_agents = [agents_in_order[-1]] + agents_in_order[:-1]

        # Assign rotated agents to roles
        for i, role in enumerate(role_order):
            if i < len(rotated_agents):
                self.roles[role] = rotated_agents[i]

    # Log the role rotation
    role_assignments = {
        role: agent.name if agent else None for role, agent in self.roles.items()
    }
    self.logger.info(f"Rotated roles for team {self.name}: {role_assignments}")

    return self.roles
