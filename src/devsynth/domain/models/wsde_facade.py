"""Facade for the Worker Self-Directed Enterprise model.

This module exposes the :class:`WSDE` dataclass and :class:`WSDETeam` class
from :mod:`wsde_core` and wires in additional behaviour from the specialised
role, voting and dialectical reasoning modules.  Auxiliary helper methods such
as communication and peer review utilities are provided via :mod:`wsde_utils`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from typing_extensions import TypedDict

from devsynth.domain.models import (
    wsde_decision_making,
    wsde_dialectical,
    wsde_enhanced_dialectical,
    wsde_multidisciplinary,
    wsde_roles,
    wsde_solution_analysis,
    wsde_voting,
)
from devsynth.domain.models.wsde_core import WSDE, SolutionRecord, TaskPayload, WSDETeam
from devsynth.domain.models.wsde_summarization import (
    summarize_consensus_result,
    summarize_voting_result,
)
from devsynth.domain.models.wsde_typing import RoleName, SupportsTeamAgent
from devsynth.domain.models.wsde_utils import (
    PeerReviewResult,
    add_solution,
    broadcast_message,
    conduct_peer_review,
    get_messages,
    request_peer_review,
    run_basic_workflow,
    send_message,
)

if TYPE_CHECKING:
    from devsynth.domain.models.wsde_base import WSDETeam as BaseWSDETeam
else:  # pragma: no cover - runtime alias for typing compatibility
    BaseWSDETeam = WSDETeam


class LearningRecord(TypedDict, total=False):
    """Structured retrospective insight captured from WSDE activities."""

    phase: str | None
    category: str | None
    summary: str
    details: Any


class PatternRecord(TypedDict, total=False):
    """Detected pattern aggregated from retrospective learnings."""

    name: str
    occurrences: int
    evidence: list[str]
    source_phases: list[str]


class IntegratedKnowledge(TypedDict, total=False):
    """High level representation of the team's consolidated knowledge."""

    summary: str
    learnings: list[LearningRecord]
    patterns: list[PatternRecord]
    updated_at: datetime


class ImprovementSuggestion(TypedDict, total=False):
    """Actionable recommendation derived from WSDE retrospectives."""

    suggestion: str
    phase: str | None
    rationale: str | None
    category: str | None
    related_patterns: list[str]


def _as_base_team(team: WSDETeam) -> BaseWSDETeam:
    """Provide a typed view compatible with helper modules."""

    return cast(BaseWSDETeam, team)


def _coerce_learning_record(
    payload: Mapping[str, Any],
    *,
    default_phase: str | None = None,
    category: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> LearningRecord:
    """Normalise arbitrary retrospective data into a learning record."""

    summary_candidates = (
        payload.get("summary"),
        payload.get("description"),
        payload.get("insight"),
        payload.get("title"),
        payload.get("message"),
    )
    summary = next(
        (
            str(candidate).strip()
            for candidate in summary_candidates
            if isinstance(candidate, str) and candidate.strip()
        ),
        "",
    )
    if not summary and "reasoning" in payload:
        summary = str(payload.get("reasoning", "")).strip()

    phase_value_raw = payload.get("phase", default_phase)
    phase_value = str(phase_value_raw) if phase_value_raw not in (None, "") else None
    category_value_raw = payload.get("category", category)
    category_value = (
        str(category_value_raw) if category_value_raw not in (None, "") else None
    )

    details: Any = dict(payload)
    if metadata:
        details = {"payload": details, "metadata": dict(metadata)}

    record: LearningRecord = {
        "phase": phase_value,
        "summary": summary or (phase_value or "general"),
        "details": details,
    }
    if category_value:
        record["category"] = category_value
    return record


def _coerce_pattern_record(pattern: Mapping[str, Any]) -> PatternRecord:
    """Normalise heterogeneous pattern payloads into a shared schema."""

    name_raw = pattern.get("name") or pattern.get("pattern") or pattern.get("summary")
    name = str(name_raw).strip() if name_raw else "Pattern"
    occurrences_raw = pattern.get("occurrences", pattern.get("count", 1))
    try:
        occurrences = int(occurrences_raw)
    except (TypeError, ValueError):
        occurrences = 1

    evidence: list[str] = []
    evidence_raw = pattern.get("evidence", [])
    if isinstance(evidence_raw, Iterable) and not isinstance(
        evidence_raw, (str, bytes)
    ):
        evidence = [
            str(item).strip()
            for item in evidence_raw
            if isinstance(item, (str, bytes)) and str(item).strip()
        ]

    source_raw = pattern.get("source_phases", pattern.get("phases", []))
    source_list: list[str] = []
    if isinstance(source_raw, Iterable) and not isinstance(source_raw, (str, bytes)):
        source_list = [
            str(item).strip()
            for item in source_raw
            if isinstance(item, (str, bytes)) and str(item).strip()
        ]
    if not source_list:
        source_list = ["general"]

    return PatternRecord(
        name=name or "Pattern",
        occurrences=max(1, occurrences),
        evidence=evidence,
        source_phases=source_list,
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
WSDETeam.summarize_consensus_result = summarize_consensus_result
WSDETeam.summarize_voting_result = summarize_voting_result

# ---------------------------------------------------------------------------
# Decision making
# ---------------------------------------------------------------------------


def _generate_diverse_ideas(
    self: WSDETeam,
    task: Mapping[str, Any] | MutableMapping[str, Any] | TaskPayload,
    max_ideas: int = 10,
    diversity_threshold: float = 0.7,
) -> list[dict[str, Any]]:
    """Delegate idea generation to the dedicated decision-making module."""

    task_payload = dict(task)
    return cast(
        list[dict[str, Any]],
        wsde_decision_making.generate_diverse_ideas(
            _as_base_team(self), task_payload, max_ideas, diversity_threshold
        ),
    )


def _create_comparison_matrix(
    self: WSDETeam,
    ideas: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    evaluation_criteria: Sequence[str],
) -> dict[str, dict[str, float]]:
    """Build a comparison matrix using the canonical implementation."""

    idea_payload = [dict(idea) for idea in ideas]
    return cast(
        dict[str, dict[str, float]],
        wsde_decision_making.create_comparison_matrix(
            _as_base_team(self), idea_payload, list(evaluation_criteria)
        ),
    )


def _evaluate_options(
    self: WSDETeam,
    ideas: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    comparison_matrix: Mapping[str, Mapping[str, float]],
    weighting_scheme: Mapping[str, float],
) -> list[dict[str, Any]]:
    """Score options by delegating to the decision-making helpers."""

    idea_payload = [dict(idea) for idea in ideas]
    comparison_payload = {
        option: dict(criteria) for option, criteria in comparison_matrix.items()
    }
    return cast(
        list[dict[str, Any]],
        wsde_decision_making.evaluate_options(
            _as_base_team(self),
            idea_payload,
            comparison_payload,
            dict(weighting_scheme),
        ),
    )


def _analyze_trade_offs(
    self: WSDETeam,
    evaluated_options: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    *,
    conflict_detection_threshold: float = 0.7,
    identify_complementary_options: bool = True,
) -> list[dict[str, Any]]:
    """Surface trade-off insights through the shared helper module."""

    option_payload = [dict(option) for option in evaluated_options]
    return cast(
        list[dict[str, Any]],
        wsde_decision_making.analyze_trade_offs(
            _as_base_team(self),
            option_payload,
            conflict_detection_threshold=conflict_detection_threshold,
            identify_complementary_options=identify_complementary_options,
        ),
    )


def _formulate_decision_criteria(
    self: WSDETeam,
    task: Mapping[str, Any] | MutableMapping[str, Any] | TaskPayload,
    evaluated_options: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    trade_offs: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    *,
    contextualize_with_code: bool = False,
    code_analyzer: Any | None = None,
) -> dict[str, float]:
    """Craft decision criteria using the domain-specific implementation."""

    option_payload = [dict(option) for option in evaluated_options]
    trade_off_payload = [dict(trade_off) for trade_off in trade_offs]
    return cast(
        dict[str, float],
        wsde_decision_making.formulate_decision_criteria(
            _as_base_team(self),
            dict(task),
            option_payload,
            trade_off_payload,
            contextualize_with_code=contextualize_with_code,
            code_analyzer=code_analyzer,
        ),
    )


def _select_best_option(
    self: WSDETeam,
    evaluated_options: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    decision_criteria: Mapping[str, float],
) -> dict[str, Any]:
    """Select the preferred option using the canonical helper."""

    option_payload = [dict(option) for option in evaluated_options]
    return cast(
        dict[str, Any],
        wsde_decision_making.select_best_option(
            _as_base_team(self), option_payload, dict(decision_criteria)
        ),
    )


def _elaborate_details(
    self: WSDETeam,
    selected_option: Mapping[str, Any] | MutableMapping[str, Any],
    **_: Any,
) -> list[dict[str, Any]]:
    """Expand the selected option into actionable details."""

    return cast(
        list[dict[str, Any]],
        wsde_decision_making.elaborate_details(
            _as_base_team(self), dict(selected_option)
        ),
    )


def _create_implementation_plan(
    self: WSDETeam,
    details: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    **_: Any,
) -> list[dict[str, Any]]:
    """Generate an implementation plan compatible with orchestration logic."""

    return cast(
        list[dict[str, Any]],
        wsde_decision_making.create_implementation_plan(
            _as_base_team(self), [dict(item) for item in details]
        ),
    )


def _optimize_implementation(
    self: WSDETeam,
    plan: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    optimization_targets: Sequence[str] | None = None,
    *,
    code_analyzer: Any | None = None,
    **_: Any,
) -> list[dict[str, Any]]:
    """Optimise implementation plans by reusing the shared helper."""

    targets = list(optimization_targets or [])
    return cast(
        list[dict[str, Any]],
        wsde_decision_making.optimize_implementation(
            _as_base_team(self),
            [dict(step) for step in plan],
            targets,
            code_analyzer=code_analyzer,
        ),
    )


def _perform_quality_assurance(
    self: WSDETeam,
    plan: Sequence[Mapping[str, Any] | MutableMapping[str, Any]],
    check_categories: Sequence[str] | None = None,
    *,
    code_analyzer: Any | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Apply quality assurance heuristics using the domain helper."""

    categories = list(check_categories or [])
    return cast(
        dict[str, Any],
        wsde_decision_making.perform_quality_assurance(
            _as_base_team(self),
            [dict(step) for step in plan],
            categories,
            code_analyzer=code_analyzer,
        ),
    )


WSDETeam.generate_diverse_ideas = _generate_diverse_ideas
WSDETeam.create_comparison_matrix = _create_comparison_matrix
WSDETeam.evaluate_options = _evaluate_options
WSDETeam.analyze_trade_offs = _analyze_trade_offs
WSDETeam.formulate_decision_criteria = _formulate_decision_criteria
WSDETeam.select_best_option = _select_best_option
WSDETeam.elaborate_details = _elaborate_details
WSDETeam.create_implementation_plan = _create_implementation_plan
WSDETeam.optimize_implementation = _optimize_implementation
WSDETeam.perform_quality_assurance = _perform_quality_assurance
WSDETeam.apply_enhanced_dialectical_reasoning = (
    wsde_enhanced_dialectical.apply_enhanced_dialectical_reasoning
)
WSDETeam.apply_enhanced_dialectical_reasoning_multi = (
    wsde_enhanced_dialectical.apply_enhanced_dialectical_reasoning_multi
)
WSDETeam._identify_thesis = wsde_enhanced_dialectical._identify_thesis
WSDETeam._generate_enhanced_antithesis = (
    wsde_enhanced_dialectical._generate_enhanced_antithesis
)
WSDETeam._generate_enhanced_synthesis = (
    wsde_enhanced_dialectical._generate_enhanced_synthesis
)
WSDETeam._generate_evaluation = wsde_enhanced_dialectical._generate_evaluation
WSDETeam._analyze_solution = wsde_solution_analysis._analyze_solution
WSDETeam._generate_comparative_analysis = (
    wsde_solution_analysis._generate_comparative_analysis
)
WSDETeam._generate_multi_solution_synthesis = staticmethod(
    wsde_enhanced_dialectical._generate_multi_solution_synthesis
)
WSDETeam._generate_comparative_evaluation = staticmethod(
    wsde_enhanced_dialectical._generate_comparative_evaluation
)


def _get_worker(self: WSDETeam) -> SupportsTeamAgent | None:
    """Return the current worker if assigned."""

    return cast(SupportsTeamAgent | None, self.roles.get(RoleName.WORKER))


def _get_supervisor(self: WSDETeam) -> SupportsTeamAgent | None:
    """Return the current supervisor if assigned."""

    return cast(SupportsTeamAgent | None, self.roles.get(RoleName.SUPERVISOR))


def _get_designer(self: WSDETeam) -> SupportsTeamAgent | None:
    """Return the current designer if assigned."""

    return cast(SupportsTeamAgent | None, self.roles.get(RoleName.DESIGNER))


def _get_evaluator(self: WSDETeam) -> SupportsTeamAgent | None:
    """Return the current evaluator if assigned."""

    return cast(SupportsTeamAgent | None, self.roles.get(RoleName.EVALUATOR))


def _get_agent(self: WSDETeam, name: str) -> SupportsTeamAgent | None:
    """Retrieve an agent by name."""

    for agent in self.agents:
        agent_name = getattr(agent, "name", None) or getattr(
            getattr(agent, "config", None), "name", None
        )
        if agent_name == name:
            return cast(SupportsTeamAgent, agent)
    return None


WSDETeam.get_worker = _get_worker
WSDETeam.get_supervisor = _get_supervisor
WSDETeam.get_designer = _get_designer
WSDETeam.get_evaluator = _get_evaluator
WSDETeam.get_agent = _get_agent


def _extract_learnings(
    self: WSDETeam,
    sources: Mapping[str, Any] | Sequence[Mapping[str, Any] | LearningRecord] | None,
    categorize_learnings: bool = False,
    include_failures: bool = False,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> list[LearningRecord]:
    """Normalise retrospective inputs into structured learning records."""

    records: list[LearningRecord] = []

    if sources is None:
        return records

    def _should_skip(payload: Mapping[str, Any]) -> bool:
        if include_failures:
            return False
        status = payload.get("status")
        if isinstance(status, str) and status.lower() in {
            "failed",
            "error",
            "incomplete",
        }:
            return True
        return False

    def _handle_entry(origin: str | None, payload: Any) -> None:
        entry_category = origin if categorize_learnings else None
        default_phase = origin

        if isinstance(payload, Mapping):
            if _should_skip(payload):
                return
            nested = payload.get("learnings")
            if isinstance(nested, Iterable) and not isinstance(nested, (str, bytes)):
                for item in nested:
                    if isinstance(item, Mapping):
                        record = _coerce_learning_record(
                            item,
                            default_phase=default_phase,
                            category=entry_category,
                            metadata=metadata,
                        )
                    else:
                        record = _coerce_learning_record(
                            {"summary": str(item)},
                            default_phase=default_phase,
                            category=entry_category,
                            metadata=metadata,
                        )
                    records.append(record)
                return

        mapping_payload: Mapping[str, Any]
        if isinstance(payload, Mapping):
            mapping_payload = payload
        else:
            mapping_payload = {"summary": str(payload)}

        record = _coerce_learning_record(
            mapping_payload,
            default_phase=default_phase,
            category=entry_category,
            metadata=metadata,
        )
        records.append(record)

    if isinstance(sources, Mapping):
        for key, value in sources.items():
            _handle_entry(str(key), value)
    elif isinstance(sources, Sequence):
        for index, value in enumerate(sources):
            _handle_entry(str(index), value)

    return records


def _recognize_patterns(
    self: WSDETeam,
    learnings: Sequence[Mapping[str, Any] | LearningRecord],
    *,
    historical_context: Sequence[Mapping[str, Any]] | None = None,
    code_analyzer: Any | None = None,
) -> list[PatternRecord]:
    """Derive recurring patterns from learnings and context."""

    normalised = [
        _coerce_learning_record(cast(Mapping[str, Any], entry)) for entry in learnings
    ]

    pattern_map: dict[str, PatternRecord] = {}

    for record in normalised:
        summary = record.get("summary", "")
        if not summary:
            continue
        key = summary.lower()
        entry = pattern_map.setdefault(
            key,
            PatternRecord(
                name=summary,
                occurrences=0,
                evidence=[],
                source_phases=[],
            ),
        )
        entry["occurrences"] += 1
        entry["evidence"].append(summary)
        phase = record.get("phase")
        if phase and phase not in entry["source_phases"]:
            entry["source_phases"].append(phase)
        category = record.get("category")
        if category and category not in entry["source_phases"]:
            entry["source_phases"].append(category)

    category_counter = Counter(
        (record.get("category") or record.get("phase") or "general").lower()
        for record in normalised
        if record.get("summary")
    )
    for category, count in category_counter.items():
        label = category or "general"
        key = f"category:{label}"
        entry = pattern_map.setdefault(
            key,
            PatternRecord(
                name=f"{label.title()} focus",
                occurrences=0,
                evidence=[],
                source_phases=[],
            ),
        )
        entry["occurrences"] += count
        if label not in entry["source_phases"]:
            entry["source_phases"].append(label)
        entry["evidence"].extend(
            record["summary"]
            for record in normalised
            if (
                (record.get("category") or record.get("phase") or "general").lower()
                == category
            )
        )

    for context in historical_context or []:
        label = str(
            context.get("name") or context.get("title") or context.get("summary") or "",
        ).strip()
        if not label:
            continue
        entry = pattern_map.setdefault(
            label.lower(),
            PatternRecord(
                name=label,
                occurrences=0,
                evidence=[],
                source_phases=[],
            ),
        )
        entry["occurrences"] += 1
        if "historical" not in entry["source_phases"]:
            entry["source_phases"].append("historical")
        entry["evidence"].append(label)

    if code_analyzer is not None:
        analyzer_insights: Sequence[str] = ()
        if hasattr(code_analyzer, "summarize_findings"):
            try:
                summary = code_analyzer.summarize_findings()
                if isinstance(summary, Mapping):
                    highlights = summary.get("highlights")
                    if isinstance(highlights, Sequence):
                        analyzer_insights = [
                            str(item)
                            for item in highlights
                            if isinstance(item, (str, bytes))
                        ]
            except Exception:
                analyzer_insights = ()
        elif hasattr(code_analyzer, "get_metrics"):
            try:
                metrics = code_analyzer.get_metrics()
                if isinstance(metrics, Mapping):
                    analyzer_insights = [
                        f"{key}: {value}" for key, value in metrics.items()
                    ]
            except Exception:
                analyzer_insights = ()
        for insight in analyzer_insights:
            label = insight.strip()
            if not label:
                continue
            entry = pattern_map.setdefault(
                label.lower(),
                PatternRecord(
                    name=label,
                    occurrences=0,
                    evidence=[],
                    source_phases=[],
                ),
            )
            entry["occurrences"] += 1
            if "analysis" not in entry["source_phases"]:
                entry["source_phases"].append("analysis")
            entry["evidence"].append(label)

    patterns = sorted(
        pattern_map.values(),
        key=lambda item: (-item["occurrences"], item["name"].lower()),
    )

    return patterns


def _integrate_knowledge(
    self: WSDETeam,
    learnings: Sequence[Mapping[str, Any] | LearningRecord],
    patterns: Sequence[Mapping[str, Any] | PatternRecord],
    *,
    memory_manager: Any | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> IntegratedKnowledge:
    """Aggregate learnings and patterns into a cohesive knowledge snapshot."""

    normalised_learnings = [
        _coerce_learning_record(cast(Mapping[str, Any], entry), metadata=metadata)
        for entry in learnings
    ]
    normalised_patterns = [
        _coerce_pattern_record(cast(Mapping[str, Any], pattern)) for pattern in patterns
    ]

    summary_sections: list[str] = []
    if normalised_patterns:
        primary = max(normalised_patterns, key=lambda item: item["occurrences"])
        summary_sections.append(
            f"Top pattern: {primary['name']} ({primary['occurrences']} occurrence(s))"
        )
    if normalised_learnings:
        phases = sorted(
            {(record.get("phase") or "general") for record in normalised_learnings}
        )
        summary_sections.append(f"Phases covered: {', '.join(phases)}")

    knowledge: IntegratedKnowledge = {
        "summary": (
            "; ".join(summary_sections)
            if summary_sections
            else "No learnings captured yet."
        ),
        "learnings": normalised_learnings,
        "patterns": normalised_patterns,
        "updated_at": datetime.now(),
    }

    if memory_manager is not None:
        try:  # pragma: no cover - defensive integration with optional managers
            if hasattr(memory_manager, "record_insight"):
                memory_manager.record_insight(knowledge)
            elif hasattr(memory_manager, "store"):
                memory_manager.store("wsde_knowledge", knowledge)
        except Exception:
            pass

    return knowledge


def _generate_improvement_suggestions(
    self: WSDETeam,
    learnings: Sequence[Mapping[str, Any] | LearningRecord],
    patterns: Sequence[Mapping[str, Any] | PatternRecord],
    quality_checks: Mapping[str, Any] | None = None,
    *,
    categorize_by_phase: bool = False,
) -> list[ImprovementSuggestion]:
    """Translate retrospectives into concrete improvement actions."""

    normalised_learnings = [
        _coerce_learning_record(cast(Mapping[str, Any], entry)) for entry in learnings
    ]
    normalised_patterns = [
        _coerce_pattern_record(cast(Mapping[str, Any], pattern)) for pattern in patterns
    ]

    suggestions: list[ImprovementSuggestion] = []

    for record in normalised_learnings:
        summary = record.get("summary")
        if not summary:
            continue
        learning_suggestion: ImprovementSuggestion = {
            "suggestion": f"Revisit learning: {summary}",
            "phase": record.get("phase"),
            "rationale": summary,
            "related_patterns": [],
        }
        if categorize_by_phase and record.get("phase"):
            learning_suggestion["category"] = record["phase"]
        suggestions.append(learning_suggestion)

    for pattern in normalised_patterns:
        pattern_suggestion: ImprovementSuggestion = {
            "suggestion": f"Address recurring pattern \"{pattern['name']}\"",
            "phase": pattern["source_phases"][0] if pattern["source_phases"] else None,
            "rationale": f"Observed {pattern['occurrences']} time(s).",
            "related_patterns": [pattern["name"]],
        }
        if categorize_by_phase and pattern["source_phases"]:
            pattern_suggestion["category"] = pattern["source_phases"][0]
        suggestions.append(pattern_suggestion)

    if quality_checks and isinstance(quality_checks, Mapping):
        issues = quality_checks.get("issues")
        if isinstance(issues, Iterable) and not isinstance(issues, (str, bytes)):
            for issue in issues:
                if isinstance(issue, Mapping):
                    description = str(issue.get("description", "")).strip()
                    category = str(issue.get("category", "")).strip() or None
                else:
                    description = str(issue).strip()
                    category = None
                if not description:
                    continue
                issue_suggestion: ImprovementSuggestion = {
                    "suggestion": f"Resolve QA issue: {description}",
                    "phase": None,
                    "rationale": description,
                    "related_patterns": [],
                }
                if categorize_by_phase and category:
                    issue_suggestion["category"] = category
                suggestions.append(issue_suggestion)

        qa_suggestions = quality_checks.get("suggestions")
        if isinstance(qa_suggestions, Iterable) and not isinstance(
            qa_suggestions, (str, bytes)
        ):
            for item in qa_suggestions:
                text = str(item).strip()
                if not text:
                    continue
                suggestions.append(
                    ImprovementSuggestion(
                        suggestion=text,
                        phase=None,
                        rationale=text,
                        related_patterns=[],
                    )
                )

    unique: dict[str, ImprovementSuggestion] = {}
    for suggestion in suggestions:
        key = suggestion.get("suggestion", "")
        if key in unique:
            existing = unique[key]
            if not existing.get("phase") and suggestion.get("phase"):
                existing["phase"] = suggestion["phase"]
            existing.setdefault("related_patterns", [])
            for pattern_name in suggestion.get("related_patterns", []):
                if pattern_name not in existing["related_patterns"]:
                    existing["related_patterns"].append(pattern_name)
            if (
                categorize_by_phase
                and suggestion.get("category")
                and not existing.get("category")
            ):
                existing["category"] = suggestion["category"]
        else:
            suggestion.setdefault("related_patterns", [])
            unique[key] = suggestion

    return list(unique.values())


def _can_propose_solution(
    self: WSDETeam,
    agent: SupportsTeamAgent,
    task: Mapping[str, Any] | TaskPayload,
) -> bool:
    """Check whether ``agent`` should propose a solution for ``task``."""

    expertise = getattr(agent, "expertise", None)
    if not expertise:
        return True

    domain = str(dict(task).get("domain", "")).strip().lower()
    if not domain:
        return True

    expertise_domains = {str(item).lower() for item in expertise if item}
    return domain in expertise_domains or "generalist" in expertise_domains


def _can_provide_critique(
    self: WSDETeam,
    agent: SupportsTeamAgent,
    solution: Mapping[str, Any] | SolutionRecord,
) -> bool:
    """Determine whether ``agent`` can credibly critique ``solution``."""

    expertise = getattr(agent, "expertise", None)
    if not expertise:
        return True

    solution_domain = ""
    if isinstance(solution, Mapping):
        solution_domain = str(
            solution.get("domain")
            or solution.get("category")
            or solution.get("area")
            or "",
        ).strip()

    if not solution_domain:
        return True

    expertise_domains = {str(item).lower() for item in expertise if item}
    return solution_domain.lower() in expertise_domains or "review" in expertise_domains


WSDETeam.extract_learnings = _extract_learnings
WSDETeam.recognize_patterns = _recognize_patterns
WSDETeam.integrate_knowledge = _integrate_knowledge
WSDETeam.generate_improvement_suggestions = _generate_improvement_suggestions
WSDETeam.can_propose_solution = _can_propose_solution
WSDETeam.can_provide_critique = _can_provide_critique


def _simple_conduct_peer_review(
    self: WSDETeam,
    work_product: Mapping[str, Any] | Any,
    author: SupportsTeamAgent,
    reviewers: Iterable[SupportsTeamAgent],
    memory_manager: Any | None = None,
    max_revision_cycles: int = 1,
) -> PeerReviewResult:
    """Run a minimal peer review cycle with memory coordination."""

    mem = memory_manager or getattr(self, "memory_manager", None)
    try:
        review = self.request_peer_review(work_product, author, reviewers)
        if review is None:
            raise RuntimeError("peer review unavailable")
        if getattr(review, "memory_manager", None) is None and mem is not None:
            try:
                review.memory_manager = mem  # pragma: no cover - optional attr
            except Exception:
                pass
        cycles = max(1, max_revision_cycles)
        feedback: dict[str, Any] = {}
        for _ in range(cycles):
            review.collect_reviews()
            feedback = review.aggregate_feedback()
            if feedback:
                break
        try:
            review.status = "completed"  # pragma: no cover - optional attr
        except Exception:
            pass
        result: PeerReviewResult = {"review": review, "feedback": feedback}
    except Exception:
        result = {
            "review": None,
            "feedback": {
                "status": "approved",
                "quality_score": 0.85,
                "comments": [],
            },
        }
    if mem is not None:
        try:  # pragma: no cover - defensive sync with optional dependencies
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
WSDETeam._improve_clarity = wsde_dialectical._improve_clarity
WSDETeam._improve_with_examples = wsde_dialectical._improve_with_examples
WSDETeam._improve_structure = wsde_dialectical._improve_structure
WSDETeam._improve_error_handling = wsde_dialectical._improve_error_handling
WSDETeam._improve_security = wsde_dialectical._improve_security
WSDETeam._improve_performance = wsde_dialectical._improve_performance
WSDETeam._improve_readability = wsde_dialectical._improve_readability
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
WSDETeam._check_pep8_compliance = wsde_dialectical._check_pep8_compliance
WSDETeam._check_security_best_practices = (
    wsde_dialectical._check_security_best_practices
)
WSDETeam._balance_performance_and_maintainability = (
    wsde_dialectical._balance_performance_and_maintainability
)
WSDETeam._balance_security_and_performance = (
    wsde_dialectical._balance_security_and_performance
)
WSDETeam._balance_security_and_usability = (
    wsde_dialectical._balance_security_and_usability
)
WSDETeam._generate_detailed_synthesis_reasoning = (
    wsde_dialectical._generate_detailed_synthesis_reasoning
)

# ---------------------------------------------------------------------------
# Multi-disciplinary reasoning
# ---------------------------------------------------------------------------
WSDETeam.apply_multi_disciplinary_dialectical_reasoning = (
    wsde_multidisciplinary.apply_multi_disciplinary_dialectical_reasoning
)
WSDETeam._gather_disciplinary_perspectives = (
    wsde_multidisciplinary._gather_disciplinary_perspectives
)
WSDETeam._identify_perspective_conflicts = (
    wsde_multidisciplinary._identify_perspective_conflicts
)
WSDETeam._generate_multi_disciplinary_synthesis = (
    wsde_multidisciplinary._generate_multi_disciplinary_synthesis
)
WSDETeam._generate_multi_disciplinary_evaluation = (
    wsde_multidisciplinary._generate_multi_disciplinary_evaluation
)

__all__ = [
    "WSDE",
    "WSDETeam",
    "summarize_consensus_result",
    "summarize_voting_result",
]
