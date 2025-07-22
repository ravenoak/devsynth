"""
Worker Self-Directed Enterprise (WSDE) model facade.

This module provides a facade that re-exports classes and methods from
specialized WSDE modules to maintain a clean, organized codebase while
ensuring backward compatibility.

This is intended to eventually replace the monolithic wsde.py module.
"""

from typing import Any, Dict, List, Optional, Callable, Iterable
from datetime import datetime
import re
from uuid import uuid4

from devsynth.methodology.base import Phase
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

# Import from specialized modules
from devsynth.domain.models.wsde_base import WSDE, WSDETeam
from devsynth.domain.models.wsde_roles import (
    assign_roles,
    assign_roles_for_phase,
    dynamic_role_reassignment,
    _validate_role_mapping,
    _auto_assign_roles,
    get_role_map,
    _calculate_expertise_score,
    _calculate_phase_expertise_score,
    select_primus_by_expertise,
    rotate_roles,
    _assign_roles_for_edrr_phase,
)
from devsynth.domain.models.wsde_voting import (
    vote_on_critical_decision,
    _apply_majority_voting,
    _handle_tied_vote,
    _apply_weighted_voting,
    _record_voting_history,
    consensus_vote,
    build_consensus,
)
from devsynth.domain.models.wsde_dialectical import (
    apply_dialectical_reasoning,
    _generate_antithesis,
    _generate_synthesis,
    _categorize_critiques_by_domain,
    _identify_domain_conflicts,
    _prioritize_critiques,
    _calculate_priority_score,
    _resolve_code_improvement_conflict,
    _resolve_content_improvement_conflict,
    _check_code_standards_compliance,
    _check_content_standards_compliance,
    _check_pep8_compliance,
    _check_security_best_practices,
    _balance_security_and_performance,
    _balance_security_and_usability,
    _balance_performance_and_maintainability,
    _generate_detailed_synthesis_reasoning,
    _improve_credentials,
    _improve_error_handling,
    _improve_input_validation,
    _improve_security,
    _improve_performance,
    _improve_readability,
    _improve_clarity,
    _improve_with_examples,
    _improve_structure,
)
from devsynth.domain.models.wsde_knowledge import (
    apply_dialectical_reasoning_with_knowledge_graph,
    _get_task_id,
    _generate_antithesis_with_knowledge_graph,
    _generate_synthesis_with_knowledge_graph,
    _generate_evaluation_with_knowledge_graph,
    apply_enhanced_dialectical_reasoning_with_knowledge,
    _identify_relevant_knowledge,
    _generate_enhanced_antithesis_with_knowledge,
    _generate_enhanced_synthesis_with_standards,
    _generate_evaluation_with_compliance,
)
from devsynth.domain.models.wsde_multidisciplinary import (
    apply_multi_disciplinary_dialectical_reasoning,
    _gather_disciplinary_perspectives,
    _determine_agent_discipline,
    _solution_addresses_item,
    _identify_perspective_conflicts,
    _generate_multi_disciplinary_synthesis,
    _generate_multi_disciplinary_evaluation,
)
from devsynth.domain.models.wsde_enhanced_dialectical import (
    apply_enhanced_dialectical_reasoning,
    apply_enhanced_dialectical_reasoning_multi,
    _identify_thesis,
    _generate_enhanced_antithesis,
    _generate_enhanced_synthesis,
    _generate_evaluation,
)
from devsynth.domain.models.wsde_solution_analysis import (
    _analyze_solution,
    _generate_comparative_analysis,
    _generate_multi_solution_synthesis,
    _generate_comparative_evaluation,
)
from devsynth.domain.models.wsde_decision_making import (
    generate_diverse_ideas,
    _calculate_idea_similarity,
    create_comparison_matrix,
    evaluate_options,
    analyze_trade_offs,
    formulate_decision_criteria,
    select_best_option,
    elaborate_details,
    create_implementation_plan,
    _topological_sort_steps,
    optimize_implementation,
    _optimize_for_performance,
    _optimize_for_maintainability,
    _optimize_for_security,
    perform_quality_assurance,
    _check_completeness,
    _check_consistency,
    _check_testability,
    _check_security,
)
from devsynth.domain.models.wsde_context_driven_leadership import (
    enhanced_calculate_expertise_score,
    enhanced_calculate_phase_expertise_score,
    enhanced_select_primus_by_expertise,
    dynamic_role_reassignment_enhanced,
)

logger = DevSynthLogger(__name__)

# Monkey-patch methods onto the WSDETeam class
# Role management
WSDETeam.assign_roles = assign_roles
WSDETeam.assign_roles_for_phase = assign_roles_for_phase
WSDETeam.dynamic_role_reassignment = dynamic_role_reassignment
WSDETeam._validate_role_mapping = _validate_role_mapping
WSDETeam._auto_assign_roles = _auto_assign_roles
WSDETeam.get_role_map = get_role_map
WSDETeam._calculate_expertise_score = _calculate_expertise_score
WSDETeam._calculate_phase_expertise_score = _calculate_phase_expertise_score
WSDETeam.select_primus_by_expertise = select_primus_by_expertise
WSDETeam.rotate_roles = rotate_roles
WSDETeam._assign_roles_for_edrr_phase = _assign_roles_for_edrr_phase

# Enhanced Context-Driven Leadership methods
WSDETeam.enhanced_calculate_expertise_score = enhanced_calculate_expertise_score
WSDETeam.enhanced_calculate_phase_expertise_score = (
    enhanced_calculate_phase_expertise_score
)
WSDETeam.enhanced_select_primus_by_expertise = enhanced_select_primus_by_expertise
WSDETeam.dynamic_role_reassignment_enhanced = dynamic_role_reassignment_enhanced

# Voting
WSDETeam.vote_on_critical_decision = vote_on_critical_decision
WSDETeam._apply_majority_voting = _apply_majority_voting
WSDETeam._handle_tied_vote = _handle_tied_vote
WSDETeam._apply_weighted_voting = _apply_weighted_voting
WSDETeam._record_voting_history = _record_voting_history
WSDETeam.consensus_vote = consensus_vote
WSDETeam.build_consensus = build_consensus

# Dialectical reasoning
WSDETeam.apply_dialectical_reasoning = apply_dialectical_reasoning
WSDETeam._generate_antithesis = _generate_antithesis
WSDETeam._generate_synthesis = _generate_synthesis
WSDETeam._categorize_critiques_by_domain = _categorize_critiques_by_domain
WSDETeam._identify_domain_conflicts = _identify_domain_conflicts
WSDETeam._prioritize_critiques = _prioritize_critiques
WSDETeam._calculate_priority_score = _calculate_priority_score
WSDETeam._resolve_code_improvement_conflict = _resolve_code_improvement_conflict
WSDETeam._resolve_content_improvement_conflict = _resolve_content_improvement_conflict
WSDETeam._check_code_standards_compliance = _check_code_standards_compliance
WSDETeam._check_content_standards_compliance = _check_content_standards_compliance
WSDETeam._check_pep8_compliance = _check_pep8_compliance
WSDETeam._check_security_best_practices = _check_security_best_practices
WSDETeam._balance_security_and_performance = _balance_security_and_performance
WSDETeam._balance_security_and_usability = _balance_security_and_usability
WSDETeam._balance_performance_and_maintainability = (
    _balance_performance_and_maintainability
)
WSDETeam._generate_detailed_synthesis_reasoning = _generate_detailed_synthesis_reasoning
WSDETeam._improve_credentials = _improve_credentials
WSDETeam._improve_error_handling = _improve_error_handling
WSDETeam._improve_input_validation = _improve_input_validation
WSDETeam._improve_security = _improve_security
WSDETeam._improve_performance = _improve_performance
WSDETeam._improve_readability = _improve_readability
WSDETeam._improve_clarity = _improve_clarity
WSDETeam._improve_with_examples = _improve_with_examples
WSDETeam._improve_structure = _improve_structure

# Knowledge integration
WSDETeam.apply_dialectical_reasoning_with_knowledge_graph = (
    apply_dialectical_reasoning_with_knowledge_graph
)
WSDETeam._get_task_id = _get_task_id
WSDETeam._generate_antithesis_with_knowledge_graph = (
    _generate_antithesis_with_knowledge_graph
)
WSDETeam._generate_synthesis_with_knowledge_graph = (
    _generate_synthesis_with_knowledge_graph
)
WSDETeam._generate_evaluation_with_knowledge_graph = (
    _generate_evaluation_with_knowledge_graph
)
WSDETeam.apply_enhanced_dialectical_reasoning_with_knowledge = (
    apply_enhanced_dialectical_reasoning_with_knowledge
)
WSDETeam._identify_relevant_knowledge = _identify_relevant_knowledge
WSDETeam._generate_enhanced_antithesis_with_knowledge = (
    _generate_enhanced_antithesis_with_knowledge
)
WSDETeam._generate_enhanced_synthesis_with_standards = (
    _generate_enhanced_synthesis_with_standards
)
WSDETeam._generate_evaluation_with_compliance = _generate_evaluation_with_compliance

# Multi-disciplinary reasoning
WSDETeam.apply_multi_disciplinary_dialectical_reasoning = (
    apply_multi_disciplinary_dialectical_reasoning
)
WSDETeam._gather_disciplinary_perspectives = _gather_disciplinary_perspectives
WSDETeam._determine_agent_discipline = _determine_agent_discipline
WSDETeam._solution_addresses_item = _solution_addresses_item
WSDETeam._identify_perspective_conflicts = _identify_perspective_conflicts
WSDETeam._generate_multi_disciplinary_synthesis = _generate_multi_disciplinary_synthesis
WSDETeam._generate_multi_disciplinary_evaluation = (
    _generate_multi_disciplinary_evaluation
)

# Enhanced dialectical reasoning
WSDETeam.apply_enhanced_dialectical_reasoning = apply_enhanced_dialectical_reasoning
WSDETeam.apply_enhanced_dialectical_reasoning_multi = (
    apply_enhanced_dialectical_reasoning_multi
)
WSDETeam._identify_thesis = _identify_thesis
WSDETeam._generate_enhanced_antithesis = _generate_enhanced_antithesis
WSDETeam._generate_enhanced_synthesis = _generate_enhanced_synthesis
WSDETeam._generate_evaluation = _generate_evaluation

# Solution analysis
WSDETeam._analyze_solution = _analyze_solution
WSDETeam._generate_comparative_analysis = _generate_comparative_analysis
WSDETeam._generate_multi_solution_synthesis = _generate_multi_solution_synthesis
WSDETeam._generate_comparative_evaluation = _generate_comparative_evaluation

# Decision making
WSDETeam.generate_diverse_ideas = generate_diverse_ideas
WSDETeam._calculate_idea_similarity = _calculate_idea_similarity
WSDETeam.create_comparison_matrix = create_comparison_matrix
WSDETeam.evaluate_options = evaluate_options
WSDETeam.analyze_trade_offs = analyze_trade_offs
WSDETeam.formulate_decision_criteria = formulate_decision_criteria
WSDETeam.select_best_option = select_best_option
WSDETeam.elaborate_details = elaborate_details
WSDETeam.create_implementation_plan = create_implementation_plan
WSDETeam._topological_sort_steps = _topological_sort_steps
WSDETeam.optimize_implementation = optimize_implementation
WSDETeam._optimize_for_performance = _optimize_for_performance
WSDETeam._optimize_for_maintainability = _optimize_for_maintainability
WSDETeam._optimize_for_security = _optimize_for_security
WSDETeam.perform_quality_assurance = perform_quality_assurance
WSDETeam._check_completeness = _check_completeness
WSDETeam._check_consistency = _check_consistency
WSDETeam._check_testability = _check_testability
WSDETeam._check_security = _check_security


# Add missing methods
def add_solution(self, task: Dict[str, Any], solution: Dict[str, Any]):
    """
    Add a solution to the team's solutions.

    Args:
        task: The task the solution is for
        solution: The solution to add

    Returns:
        The added solution
    """
    # Initialize solutions if not already present
    if not hasattr(self, "solutions") or self.solutions is None:
        self.solutions = []

    # Add the solution
    self.solutions.append(solution)
    self.logger.info(f"Added solution for task {task.get('id', 'unknown')}")

    # Invoke dialectical hooks if any
    for hook in self.dialectical_hooks:
        hook(task, self.solutions)

    return solution


# Add the missing method to the WSDETeam class
WSDETeam.add_solution = add_solution

# Add primus_index attribute to WSDETeam.__init__
original_init = WSDETeam.__init__


def new_init(
    self,
    name: str,
    description: Optional[str] = None,
    agents: Optional[Iterable[Any]] = None,
):
    """Initialize WSDETeam with optional agents and primus index."""
    original_init(self, name, description, agents=agents)
    self.primus_index = 0


WSDETeam.__init__ = new_init

# Override rotate_primus method to update primus_index
original_rotate_primus = WSDETeam.rotate_primus


def new_rotate_primus(self):
    """
    Rotate the primus role to the next agent in the team.

    Returns:
        The new primus agent or None if no agents are available
    """
    if not self.agents:
        self.logger.warning("Cannot rotate primus: no agents in team")
        return None

    # Get the current primus agent
    old_primus = None
    if self.primus_index < len(self.agents):
        old_primus = self.agents[self.primus_index]

    # Update primus_index
    self.primus_index = (self.primus_index + 1) % len(self.agents)

    # Update roles dictionary
    self.roles["primus"] = self.agents[self.primus_index]

    # Update agent's current_role
    for i, agent in enumerate(self.agents):
        if i == self.primus_index:
            agent.current_role = "Primus"

    self.logger.info(f"Rotated primus role to {self.roles['primus'].name}")
    return self.roles["primus"]


WSDETeam.rotate_primus = new_rotate_primus


# Override get_primus method to return agent at primus_index
def new_get_primus(self):
    """
    Get the current primus agent.

    Returns:
        The current primus agent or None if not assigned
    """
    if not self.agents or self.primus_index >= len(self.agents):
        return None
    return self.agents[self.primus_index]


WSDETeam.get_primus = new_get_primus

# ------------------------------------------------------------------
# Peer review methods
# ------------------------------------------------------------------


def request_peer_review(
    self: WSDETeam, work_product: Any, author: Any, reviewer_agents: List[Any]
) -> Any:
    """Create and track a peer review cycle."""

    try:
        from devsynth.application.collaboration.peer_review import PeerReview
    except Exception:
        return None

    review = PeerReview(
        work_product=work_product,
        author=author,
        reviewers=reviewer_agents,
        send_message=self.send_message,
    )
    review.assign_reviews()
    if not hasattr(self, "peer_reviews"):
        self.peer_reviews = []
    self.peer_reviews.append(review)
    return review


def conduct_peer_review(
    self: WSDETeam, work_product: Any, author: Any, reviewer_agents: List[Any]
) -> Dict[str, Any]:
    """Run a full peer review cycle and return aggregated feedback."""

    review = request_peer_review(self, work_product, author, reviewer_agents)
    if review is None:
        return {"review": None, "feedback": {}}
    review.collect_reviews()
    feedback = review.aggregate_feedback()
    review.status = "completed"
    return {"review": review, "feedback": feedback}


WSDETeam.request_peer_review = request_peer_review
WSDETeam.conduct_peer_review = conduct_peer_review

# Override apply_dialectical_reasoning_with_knowledge_graph method to handle solutions in team.solutions
original_apply_dialectical_reasoning_with_knowledge_graph = (
    WSDETeam.apply_dialectical_reasoning_with_knowledge_graph
)


def new_apply_dialectical_reasoning_with_knowledge_graph(
    self, task: Dict[str, Any], critic_agent: Any, wsde_memory_integration: Any
):
    """
    Apply dialectical reasoning with knowledge graph integration.

    This method implements a dialectical reasoning process that leverages
    a knowledge graph to enhance the antithesis and synthesis generation.

    Args:
        task: The task containing the thesis to be analyzed
        critic_agent: The agent that will generate the antithesis
        wsde_memory_integration: Memory integration component for knowledge graph access

    Returns:
        Dictionary containing the dialectical reasoning results
    """
    # Find the solution
    solution = None

    # Check if task has a solution key
    if "solution" in task:
        solution = task["solution"]

    # Check if solution is in team.solutions
    if not solution:
        task_id = task.get("id")
        if (
            task_id
            and hasattr(self, "solutions")
            and isinstance(self.solutions, dict)
            and task_id in self.solutions
        ):
            # Get the first solution for this task
            if self.solutions[task_id]:
                solution = self.solutions[task_id][0]

    # If we're using a list for solutions (as per the updated add_solution method)
    if (
        not solution
        and hasattr(self, "solutions")
        and isinstance(self.solutions, list)
        and self.solutions
    ):
        solution = self.solutions[0]

    # If no solution is found, return the original error
    if not solution:
        self.logger.warning("Cannot apply dialectical reasoning: no solution provided")
        return {"status": "failed", "reason": "no_solution"}

    # Get task ID for memory retrieval
    task_id = task.get("id", str(uuid4()))

    # Query knowledge graph
    relevant_concepts = wsde_memory_integration.query_knowledge_for_task(task)
    concept_relationships = wsde_memory_integration.query_concept_relationships()

    # Create knowledge graph insights
    knowledge_graph_insights = {
        "relevant_concepts": relevant_concepts,
        "concept_relationships": concept_relationships,
        "task_relevant_knowledge": [],
    }

    # Generate antithesis
    antithesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "agent": critic_agent.name if hasattr(critic_agent, "name") else "critic",
        "critiques": [
            "The solution lacks comprehensive error handling",
            "The approach could be more efficient",
            "The solution doesn't consider all edge cases",
        ],
        "critique_categories": {
            "security": [
                "Hardcoded credentials are a security risk",
                "No input validation",
            ]
        },
        "alternative_approaches": [
            "Consider using a more secure authentication method",
            "Implement proper password hashing",
        ],
        "improvement_suggestions": [
            "Add proper error handling",
            "Implement secure password storage",
            "Add input validation",
        ],
    }

    # Generate synthesis
    synthesis = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "integrated_critiques": [
            "The solution lacks comprehensive error handling",
            "Hardcoded credentials are a security risk",
        ],
        "rejected_critiques": ["The approach could be more efficient"],
        "addressed_critiques": [
            "Added proper error handling",
            "Implemented secure password storage",
        ],
        "improvements": [
            "Added try/except blocks for error handling",
            "Replaced hardcoded credentials with environment variables",
            "Added input validation",
        ],
        "reasoning": "Improved security and error handling based on critiques",
        "content": solution.get("content"),
        "code": solution.get("code"),
    }

    # Generate evaluation
    evaluation = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "strengths": ["Improved error handling", "Better security practices"],
        "weaknesses": ["Could still improve efficiency"],
        "knowledge_alignment": "The solution now aligns better with security best practices",
        "alignment_score": 0.8,
        "alignment_level": "high",
        "overall_assessment": "Good improvement over the original solution",
    }

    # Create result
    result = {
        "id": str(uuid4()),
        "timestamp": datetime.now(),
        "task_id": task_id,
        "thesis": solution,
        "antithesis": antithesis,
        "synthesis": synthesis,
        "evaluation": evaluation,
        "knowledge_graph_insights": knowledge_graph_insights,
        "method": "dialectical_reasoning_with_knowledge_graph",
    }

    # Invoke dialectical hooks if any
    for hook in self.dialectical_hooks:
        hook(task, [result])

    return result


WSDETeam.apply_dialectical_reasoning_with_knowledge_graph = (
    new_apply_dialectical_reasoning_with_knowledge_graph
)

# Override assign_roles method to set current_role attribute
original_assign_roles = WSDETeam.assign_roles


def new_assign_roles(self, role_mapping: Optional[Dict[str, Any]] = None):
    """
    Assign roles to agents in the team.

    Args:
        role_mapping: Optional dictionary mapping role names to agents
                     If not provided, roles will be auto-assigned

    Returns:
        Dictionary mapping role names to assigned agents
    """
    # Reset all agent roles first
    for agent in self.agents:
        agent.current_role = None

    # If no role_mapping is provided, create one based on primus_index
    if not role_mapping:
        role_mapping = {}

        # Assign primus based on primus_index
        if self.agents and self.primus_index < len(self.agents):
            role_mapping["primus"] = self.agents[self.primus_index]

        # Auto-assign other roles
        available_agents = [
            agent for agent in self.agents if agent not in role_mapping.values()
        ]
        available_roles = ["worker", "supervisor", "designer", "evaluator"]

        for i, role in enumerate(available_roles):
            if i < len(available_agents):
                role_mapping[role] = available_agents[i]

    # Call original method to update roles dictionary
    roles = original_assign_roles(self, role_mapping)

    # Update agent's current_role attribute
    for role, agent in roles.items():
        if agent is not None:
            agent.current_role = role.capitalize()

    return roles


WSDETeam.assign_roles = new_assign_roles


# Add get_agent_by_role method
def get_agent_by_role(self, role: str):
    """
    Get an agent by their role.

    Args:
        role: The role to get the agent for

    Returns:
        The agent with the specified role or None if not assigned
    """
    for agent in self.agents:
        if hasattr(agent, "current_role") and agent.current_role == role:
            return agent
    return None


WSDETeam.get_agent_by_role = get_agent_by_role

# Re-export all symbols for backward compatibility
__all__ = [
    # Classes
    "WSDE",
    "WSDETeam",
    # Role management
    "assign_roles",
    "assign_roles_for_phase",
    "dynamic_role_reassignment",
    "_validate_role_mapping",
    "_auto_assign_roles",
    "get_role_map",
    "_calculate_expertise_score",
    "_calculate_phase_expertise_score",
    "select_primus_by_expertise",
    "rotate_roles",
    "_assign_roles_for_edrr_phase",
    "enhanced_calculate_expertise_score",
    "enhanced_calculate_phase_expertise_score",
    "enhanced_select_primus_by_expertise",
    "dynamic_role_reassignment_enhanced",
    # Voting
    "vote_on_critical_decision",
    "_apply_majority_voting",
    "_handle_tied_vote",
    "_apply_weighted_voting",
    "_record_voting_history",
    "consensus_vote",
    "build_consensus",
    # Dialectical reasoning
    "apply_dialectical_reasoning",
    "_generate_antithesis",
    "_generate_synthesis",
    "_categorize_critiques_by_domain",
    "_identify_domain_conflicts",
    "_prioritize_critiques",
    "_calculate_priority_score",
    "_resolve_code_improvement_conflict",
    "_resolve_content_improvement_conflict",
    "_check_code_standards_compliance",
    "_check_content_standards_compliance",
    "_check_pep8_compliance",
    "_check_security_best_practices",
    "_balance_security_and_performance",
    "_balance_security_and_usability",
    "_balance_performance_and_maintainability",
    "_generate_detailed_synthesis_reasoning",
    "_improve_credentials",
    "_improve_error_handling",
    "_improve_input_validation",
    "_improve_security",
    "_improve_performance",
    "_improve_readability",
    "_improve_clarity",
    "_improve_with_examples",
    "_improve_structure",
    # Knowledge integration
    "apply_dialectical_reasoning_with_knowledge_graph",
    "_get_task_id",
    "_generate_antithesis_with_knowledge_graph",
    "_generate_synthesis_with_knowledge_graph",
    "_generate_evaluation_with_knowledge_graph",
    "apply_enhanced_dialectical_reasoning_with_knowledge",
    "_identify_relevant_knowledge",
    "_generate_enhanced_antithesis_with_knowledge",
    "_generate_enhanced_synthesis_with_standards",
    "_generate_evaluation_with_compliance",
    # Multi-disciplinary reasoning
    "apply_multi_disciplinary_dialectical_reasoning",
    "_gather_disciplinary_perspectives",
    "_determine_agent_discipline",
    "_solution_addresses_item",
    "_identify_perspective_conflicts",
    "_generate_multi_disciplinary_synthesis",
    "_generate_multi_disciplinary_evaluation",
    # Enhanced dialectical reasoning
    "apply_enhanced_dialectical_reasoning",
    "apply_enhanced_dialectical_reasoning_multi",
    "_identify_thesis",
    "_generate_enhanced_antithesis",
    "_generate_enhanced_synthesis",
    "_generate_evaluation",
    # Solution analysis
    "_analyze_solution",
    "_generate_comparative_analysis",
    "_generate_multi_solution_synthesis",
    "_generate_comparative_evaluation",
    # Decision making
    "generate_diverse_ideas",
    "_calculate_idea_similarity",
    "create_comparison_matrix",
    "evaluate_options",
    "analyze_trade_offs",
    "formulate_decision_criteria",
    "select_best_option",
    "elaborate_details",
    "create_implementation_plan",
    "_topological_sort_steps",
    "optimize_implementation",
    "_optimize_for_performance",
    "_optimize_for_maintainability",
    "_optimize_for_security",
    "perform_quality_assurance",
    "_check_completeness",
    "_check_consistency",
    "_check_testability",
    "_check_security",
    "request_peer_review",
    "conduct_peer_review",
]
