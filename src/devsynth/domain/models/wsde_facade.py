"""Facade for the Worker Self-Directed Enterprise model.

This module exposes the :class:`WSDE` dataclass and :class:`WSDETeam` class
from :mod:`wsde_core` and wires in additional behaviour from the specialised
role, voting and dialectical reasoning modules.  Auxiliary helper methods such
as communication and peer review utilities are provided via :mod:`wsde_utils`.
"""

from __future__ import annotations

from devsynth.domain.models import wsde_dialectical, wsde_roles, wsde_voting
from devsynth.domain.models.wsde_core import WSDE, WSDETeam
from devsynth.domain.models.wsde_utils import (
    add_solution,
    broadcast_message,
    conduct_peer_review,
    get_messages,
    request_peer_review,
    send_message,
)

# ---------------------------------------------------------------------------
# Attach utility helpers
# ---------------------------------------------------------------------------
WSDETeam.send_message = send_message
WSDETeam.broadcast_message = broadcast_message
WSDETeam.get_messages = get_messages
WSDETeam.request_peer_review = request_peer_review
WSDETeam.conduct_peer_review = conduct_peer_review
WSDETeam.add_solution = add_solution

# ---------------------------------------------------------------------------
# Role management
# ---------------------------------------------------------------------------
WSDETeam.assign_roles = wsde_roles.assign_roles
WSDETeam.assign_roles_for_phase = wsde_roles.assign_roles_for_phase
WSDETeam.dynamic_role_reassignment = wsde_roles.dynamic_role_reassignment
WSDETeam._validate_role_mapping = wsde_roles._validate_role_mapping
WSDETeam._auto_assign_roles = wsde_roles._auto_assign_roles
WSDETeam.get_role_map = wsde_roles.get_role_map
WSDETeam._calculate_expertise_score = wsde_roles._calculate_expertise_score
WSDETeam._calculate_phase_expertise_score = wsde_roles._calculate_phase_expertise_score
WSDETeam.select_primus_by_expertise = wsde_roles.select_primus_by_expertise
WSDETeam.rotate_roles = wsde_roles.rotate_roles
WSDETeam._assign_roles_for_edrr_phase = wsde_roles._assign_roles_for_edrr_phase

# ---------------------------------------------------------------------------
# Voting
# ---------------------------------------------------------------------------
WSDETeam.vote_on_critical_decision = wsde_voting.vote_on_critical_decision
WSDETeam._apply_majority_voting = wsde_voting._apply_majority_voting
WSDETeam._handle_tied_vote = wsde_voting._handle_tied_vote
WSDETeam._apply_weighted_voting = wsde_voting._apply_weighted_voting
WSDETeam._record_voting_history = wsde_voting._record_voting_history
WSDETeam.consensus_vote = wsde_voting.consensus_vote
WSDETeam.build_consensus = wsde_voting.build_consensus

# ---------------------------------------------------------------------------
# Dialectical reasoning
# ---------------------------------------------------------------------------
WSDETeam.apply_dialectical_reasoning = wsde_dialectical.apply_dialectical_reasoning
WSDETeam._generate_antithesis = wsde_dialectical._generate_antithesis
WSDETeam._generate_synthesis = wsde_dialectical._generate_synthesis
WSDETeam._categorize_critiques_by_domain = (
    wsde_dialectical._categorize_critiques_by_domain
)
WSDETeam._identify_domain_conflicts = wsde_dialectical._identify_domain_conflicts
WSDETeam._prioritize_critiques = wsde_dialectical._prioritize_critiques
WSDETeam._calculate_priority_score = wsde_dialectical._calculate_priority_score
WSDETeam._resolve_code_improvement_conflict = (
    wsde_dialectical._resolve_code_improvement_conflict
)
WSDETeam._resolve_content_improvement_conflict = (
    wsde_dialectical._resolve_content_improvement_conflict
)
WSDETeam._check_code_standards_compliance = (
    wsde_dialectical._check_code_standards_compliance
)
WSDETeam._check_content_standards_compliance = (
    wsde_dialectical._check_content_standards_compliance
)
WSDETeam._generate_detailed_synthesis_reasoning = (
    wsde_dialectical._generate_detailed_synthesis_reasoning
)

__all__ = ["WSDE", "WSDETeam"]
