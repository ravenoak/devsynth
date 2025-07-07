"""
Worker Self-Directed Enterprise (WSDE) model facade.

This module provides a facade that re-exports classes and methods from
specialized WSDE modules to maintain a clean, organized codebase while
ensuring backward compatibility.

This is intended to eventually replace the monolithic wsde.py module.
"""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import re

from devsynth.methodology.base import Phase
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError

# Import from specialized modules
from devsynth.domain.models.wsde_base import WSDE, WSDETeam
from devsynth.domain.models.wsde_roles import (
    assign_roles, assign_roles_for_phase, dynamic_role_reassignment,
    _validate_role_mapping, _auto_assign_roles, get_role_map,
    _calculate_expertise_score, _calculate_phase_expertise_score,
    select_primus_by_expertise, rotate_roles, _assign_roles_for_edrr_phase
)
from devsynth.domain.models.wsde_voting import (
    vote_on_critical_decision, _apply_majority_voting, _handle_tied_vote,
    _apply_weighted_voting, _record_voting_history, consensus_vote, build_consensus
)
from devsynth.domain.models.wsde_dialectical import (
    apply_dialectical_reasoning, _generate_antithesis, _generate_synthesis,
    _categorize_critiques_by_domain, _identify_domain_conflicts, _prioritize_critiques,
    _calculate_priority_score, _resolve_code_improvement_conflict,
    _resolve_content_improvement_conflict, _check_code_standards_compliance,
    _check_content_standards_compliance, _check_pep8_compliance,
    _check_security_best_practices, _balance_security_and_performance,
    _balance_security_and_usability, _balance_performance_and_maintainability,
    _generate_detailed_synthesis_reasoning, _improve_credentials,
    _improve_error_handling, _improve_input_validation, _improve_security,
    _improve_performance, _improve_readability, _improve_clarity,
    _improve_with_examples, _improve_structure
)
from devsynth.domain.models.wsde_knowledge import (
    apply_dialectical_reasoning_with_knowledge_graph, _get_task_id,
    _generate_antithesis_with_knowledge_graph, _generate_synthesis_with_knowledge_graph,
    _generate_evaluation_with_knowledge_graph, apply_enhanced_dialectical_reasoning_with_knowledge,
    _identify_relevant_knowledge, _generate_enhanced_antithesis_with_knowledge,
    _generate_enhanced_synthesis_with_standards, _generate_evaluation_with_compliance
)
from devsynth.domain.models.wsde_multidisciplinary import (
    apply_multi_disciplinary_dialectical_reasoning, _gather_disciplinary_perspectives,
    _determine_agent_discipline, _solution_addresses_item, _identify_perspective_conflicts,
    _generate_multi_disciplinary_synthesis, _generate_multi_disciplinary_evaluation
)
from devsynth.domain.models.wsde_enhanced_dialectical import (
    apply_enhanced_dialectical_reasoning, apply_enhanced_dialectical_reasoning_multi,
    _identify_thesis, _generate_enhanced_antithesis, _generate_enhanced_synthesis,
    _generate_evaluation
)
from devsynth.domain.models.wsde_solution_analysis import (
    _analyze_solution, _generate_comparative_analysis, _generate_multi_solution_synthesis,
    _generate_comparative_evaluation
)
from devsynth.domain.models.wsde_decision_making import (
    generate_diverse_ideas, _calculate_idea_similarity, create_comparison_matrix,
    evaluate_options, analyze_trade_offs, formulate_decision_criteria,
    select_best_option, elaborate_details, create_implementation_plan,
    _topological_sort_steps, optimize_implementation, _optimize_for_performance,
    _optimize_for_maintainability, _optimize_for_security, perform_quality_assurance,
    _check_completeness, _check_consistency, _check_testability, _check_security
)

logger = DevSynthLogger(__name__)

# Re-export all symbols for backward compatibility
__all__ = [
    # Classes
    'WSDE', 'WSDETeam',
    
    # Role management
    'assign_roles', 'assign_roles_for_phase', 'dynamic_role_reassignment',
    '_validate_role_mapping', '_auto_assign_roles', 'get_role_map',
    '_calculate_expertise_score', '_calculate_phase_expertise_score',
    'select_primus_by_expertise', 'rotate_roles', '_assign_roles_for_edrr_phase',
    
    # Voting
    'vote_on_critical_decision', '_apply_majority_voting', '_handle_tied_vote',
    '_apply_weighted_voting', '_record_voting_history', 'consensus_vote', 'build_consensus',
    
    # Dialectical reasoning
    'apply_dialectical_reasoning', '_generate_antithesis', '_generate_synthesis',
    '_categorize_critiques_by_domain', '_identify_domain_conflicts', '_prioritize_critiques',
    '_calculate_priority_score', '_resolve_code_improvement_conflict',
    '_resolve_content_improvement_conflict', '_check_code_standards_compliance',
    '_check_content_standards_compliance', '_check_pep8_compliance',
    '_check_security_best_practices', '_balance_security_and_performance',
    '_balance_security_and_usability', '_balance_performance_and_maintainability',
    '_generate_detailed_synthesis_reasoning', '_improve_credentials',
    '_improve_error_handling', '_improve_input_validation', '_improve_security',
    '_improve_performance', '_improve_readability', '_improve_clarity',
    '_improve_with_examples', '_improve_structure',
    
    # Knowledge integration
    'apply_dialectical_reasoning_with_knowledge_graph', '_get_task_id',
    '_generate_antithesis_with_knowledge_graph', '_generate_synthesis_with_knowledge_graph',
    '_generate_evaluation_with_knowledge_graph', 'apply_enhanced_dialectical_reasoning_with_knowledge',
    '_identify_relevant_knowledge', '_generate_enhanced_antithesis_with_knowledge',
    '_generate_enhanced_synthesis_with_standards', '_generate_evaluation_with_compliance',
    
    # Multi-disciplinary reasoning
    'apply_multi_disciplinary_dialectical_reasoning', '_gather_disciplinary_perspectives',
    '_determine_agent_discipline', '_solution_addresses_item', '_identify_perspective_conflicts',
    '_generate_multi_disciplinary_synthesis', '_generate_multi_disciplinary_evaluation',
    
    # Enhanced dialectical reasoning
    'apply_enhanced_dialectical_reasoning', 'apply_enhanced_dialectical_reasoning_multi',
    '_identify_thesis', '_generate_enhanced_antithesis', '_generate_enhanced_synthesis',
    '_generate_evaluation',
    
    # Solution analysis
    '_analyze_solution', '_generate_comparative_analysis', '_generate_multi_solution_synthesis',
    '_generate_comparative_evaluation',
    
    # Decision making
    'generate_diverse_ideas', '_calculate_idea_similarity', 'create_comparison_matrix',
    'evaluate_options', 'analyze_trade_offs', 'formulate_decision_criteria',
    'select_best_option', 'elaborate_details', 'create_implementation_plan',
    '_topological_sort_steps', 'optimize_implementation', '_optimize_for_performance',
    '_optimize_for_maintainability', '_optimize_for_security', 'perform_quality_assurance',
    '_check_completeness', '_check_consistency', '_check_testability', '_check_security'
]