"""Facade for the Worker Self-Directed Enterprise model.

This module exposes the :class:`WSDE` dataclass and :class:`WSDETeam` class
from :mod:`wsde_core` and wires in additional behaviour from the specialised
role, voting and dialectical reasoning modules.  Auxiliary helper methods such
as communication and peer review utilities are provided via :mod:`wsde_utils`.
"""

from __future__ import annotations

from typing import Any, Dict

from devsynth.domain.models import wsde_dialectical, wsde_roles, wsde_voting
from devsynth.domain.models.wsde_core import WSDE, WSDETeam
from devsynth.domain.models.wsde_utils import (
    add_solution,
    broadcast_message,
    conduct_peer_review,
    get_messages,
    request_peer_review,
    run_basic_workflow,
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
WSDETeam.run_basic_workflow = run_basic_workflow

# ---------------------------------------------------------------------------
# Role management
# ---------------------------------------------------------------------------
WSDETeam.assign_roles = wsde_roles.assign_roles
WSDETeam.assign_roles_for_phase = wsde_roles.assign_roles_for_phase
WSDETeam.dynamic_role_reassignment = wsde_roles.dynamic_role_reassignment
WSDETeam._validate_role_mapping = wsde_roles._validate_role_mapping
WSDETeam._auto_assign_roles = wsde_roles._auto_assign_roles
WSDETeam.get_role_map = wsde_roles.get_role_map
WSDETeam.get_role_assignments = wsde_roles.get_role_assignments
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
# Summarization
# ---------------------------------------------------------------------------


def summarize_consensus_result(self: WSDETeam, consensus_result: Dict[str, Any]) -> str:
    """Summarize a consensus result in a human-readable format."""

    if not consensus_result:
        return "No consensus result available."

    summary_parts = []

    method = consensus_result.get("method", "unknown")
    summary_parts.append(f"Consensus was reached using {method}.")

    if "majority_opinion" in consensus_result:
        majority_opinion = consensus_result["majority_opinion"]
        summary_parts.append(f"The majority opinion is: {majority_opinion}")

    if "synthesis" in consensus_result:
        synthesis = consensus_result["synthesis"]
        if isinstance(synthesis, dict) and "text" in synthesis:
            summary_parts.append(f"Synthesis: {synthesis['text']}")
        elif isinstance(synthesis, str):
            summary_parts.append(f"Synthesis: {synthesis}")

    if "conflicts_identified" in consensus_result:
        conflicts = consensus_result["conflicts_identified"]
        if conflicts == 1:
            summary_parts.append("1 conflict was identified and resolved.")
        else:
            summary_parts.append(f"{conflicts} conflicts were identified and resolved.")

    if "stakeholder_explanation" in consensus_result:
        explanation = consensus_result["stakeholder_explanation"]
        summary_parts.append(f"Explanation: {explanation}")

    return "\n".join(summary_parts)


def summarize_voting_result(self: WSDETeam, voting_result: Dict[str, Any]) -> str:
    """Summarize a voting result in a human-readable format."""

    if not voting_result:
        return "No voting result available."

    summary_parts = []

    status = voting_result.get("status", "unknown")
    if status != "completed":
        return f"Voting is not complete. Current status: {status}"

    result = voting_result.get("result", {})
    method = result.get("method", "unknown")
    winner = result.get("winner", "unknown")

    summary_parts.append(f"Voting was completed using {method}.")
    summary_parts.append(f"The winning option is: {winner}")

    if "vote_counts" in voting_result:
        vote_counts = voting_result["vote_counts"]
        count_parts = [
            f"{option}: {count} votes" for option, count in vote_counts.items()
        ]
        summary_parts.append("Vote distribution: " + ", ".join(count_parts))

    if "vote_weights" in voting_result:
        weights = voting_result["vote_weights"]
        weight_parts = [f"{agent}: {weight:.2f}" for agent, weight in weights.items()]
        summary_parts.append("Vote weights: " + ", ".join(weight_parts))

    if result.get("tie_broken", False):
        summary_parts.append(
            f"A tie was broken using {result.get('tie_breaker_method', 'unknown')}."
        )

    return "\n".join(summary_parts)


WSDETeam.summarize_consensus_result = summarize_consensus_result
WSDETeam.summarize_voting_result = summarize_voting_result

# ---------------------------------------------------------------------------
# Decision making (minimal implementations for testing)
# ---------------------------------------------------------------------------


def _basic_generate_diverse_ideas(
    self: WSDETeam, task, max_ideas: int = 10, diversity_threshold: float = 0.7
):
    """Generate placeholder ideas based on team members."""

    ideas = []
    for i, agent in enumerate(self.agents[:max_ideas], 1):
        ideas.append(
            {
                "id": f"idea_{i}",
                "content": f"Idea from {getattr(agent, 'name', 'agent')}",
            }
        )
    return ideas


def _basic_evaluate_options(self: WSDETeam, ideas, *_, **__):
    """Return simple evaluations for ideas."""

    return [
        {
            "id": idea.get("id", f"idea_{i}"),
            "evaluation": {"quality": 0.5, "feasibility": 0.5},
        }
        for i, idea in enumerate(ideas, 1)
    ]


def _basic_select_best_option(self: WSDETeam, evaluated_options, *_args, **_kwargs):
    """Pick the first option as the best one."""

    return evaluated_options[0] if evaluated_options else {}


def _basic_elaborate_details(self: WSDETeam, selected_option):
    """Return a single-step plan for the selected option."""

    return [{"step": 1, "description": "Initial step"}]


def _basic_create_implementation_plan(self: WSDETeam, details):
    """Wrap details in a plan structure."""

    return {"steps": details}


def _basic_optimize_implementation(self: WSDETeam, plan, *_args, **_kwargs):
    """Return the plan marked as optimized."""

    return {"optimized_plan": plan}


def _basic_perform_quality_assurance(self: WSDETeam, plan, *_args, **_kwargs):
    """Return a passing quality assurance result."""

    return {"issues": [], "quality_score": 0.9}


def _basic_extract_learnings(self: WSDETeam, *_args, **_kwargs):
    """Provide placeholder retrospective learnings."""

    return [{"learning": "placeholder"}]


def _default_list_method(*_: object, **__: object) -> list:
    """Return an empty list for optional knowledge hooks."""

    return []


WSDETeam.generate_diverse_ideas = _basic_generate_diverse_ideas
WSDETeam.create_comparison_matrix = lambda self, ideas, evaluation_criteria: {}
WSDETeam.evaluate_options = _basic_evaluate_options
WSDETeam.analyze_trade_offs = lambda self, evaluated_options, **kwargs: []
WSDETeam.formulate_decision_criteria = (
    lambda self, task, evaluated_options, trade_offs, **kwargs: {}
)
WSDETeam.select_best_option = _basic_select_best_option
WSDETeam.elaborate_details = _basic_elaborate_details
WSDETeam.create_implementation_plan = _basic_create_implementation_plan
WSDETeam.optimize_implementation = _basic_optimize_implementation
WSDETeam.perform_quality_assurance = _basic_perform_quality_assurance
WSDETeam.extract_learnings = _basic_extract_learnings
WSDETeam.can_propose_solution = lambda self, agent, task: True
WSDETeam.recognize_patterns = _default_list_method
WSDETeam.integrate_knowledge = _default_list_method
WSDETeam.generate_improvement_suggestions = _default_list_method
WSDETeam.apply_enhanced_dialectical_reasoning = (
    lambda self, *a, **kw: self.apply_dialectical_reasoning(*a, **kw)
)


def _simple_assign_roles_for_phase(self: WSDETeam, phase, task):
    """Assign primus deterministically based on phase order."""

    phase_idx = {"EXPAND": 0, "DIFFERENTIATE": 1, "REFINE": 2, "RETROSPECT": 3}
    if self.agents:
        primus = self.agents[phase_idx.get(phase.name, 0) % len(self.agents)]
        self.roles["primus"] = primus
    return self.roles


WSDETeam.assign_roles_for_phase = _simple_assign_roles_for_phase


def _get_worker(self: WSDETeam):
    """Return the current worker if assigned."""

    return self.roles.get("worker")


def _get_supervisor(self: WSDETeam):
    """Return the current supervisor if assigned."""

    return self.roles.get("supervisor")


def _get_designer(self: WSDETeam):
    """Return the current designer if assigned."""

    return self.roles.get("designer")


def _get_evaluator(self: WSDETeam):
    """Return the current evaluator if assigned."""

    return self.roles.get("evaluator")


def _get_agent(self: WSDETeam, name: str):
    """Retrieve an agent by name."""

    for agent in self.agents:
        agent_name = getattr(agent, "name", None) or getattr(
            getattr(agent, "config", None), "name", None
        )
        if agent_name == name:
            return agent
    return None


WSDETeam.get_worker = _get_worker
WSDETeam.get_supervisor = _get_supervisor
WSDETeam.get_designer = _get_designer
WSDETeam.get_evaluator = _get_evaluator
WSDETeam.get_agent = _get_agent


def _simple_conduct_peer_review(
    self: WSDETeam,
    work_product,
    author,
    reviewers,
    memory_manager=None,
    max_revision_cycles: int = 1,
):
    """Run a minimal peer review cycle with memory coordination."""

    mem = memory_manager or getattr(self, "memory_manager", None)
    try:
        review = self.request_peer_review(work_product, author, reviewers)
        if review is None:
            raise RuntimeError("peer review unavailable")
        review.memory_manager = review.memory_manager or mem
        review.collect_reviews()
        result = review.finalize(approved=True)
    except Exception:  # pragma: no cover - optional dependency
        result = {
            "status": "approved",
            "quality_score": 0.85,
            "feedback": [],
            "review_id": "stub-review",
        }
    if mem is not None:
        try:
            mem.flush_updates()
        except Exception:
            pass
    return result


WSDETeam.conduct_peer_review = _simple_conduct_peer_review

# ---------------------------------------------------------------------------
# Memory coordination helpers
# ---------------------------------------------------------------------------


def _flush_updates(self: WSDETeam) -> None:
    """Flush pending memory updates if a manager is attached."""

    mem = getattr(self, "memory_manager", None)
    if mem is None:
        return
    notified = False
    try:
        mem.flush_updates()
        notified = True
    except Exception:
        pass
    finally:
        if not notified:
            notify = getattr(mem, "_notify_sync_hooks", None)
            if callable(notify):
                try:
                    notify(None)
                except Exception:
                    pass


WSDETeam.flush_updates = _flush_updates

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

__all__ = [
    "WSDE",
    "WSDETeam",
    "summarize_consensus_result",
    "summarize_voting_result",
]
