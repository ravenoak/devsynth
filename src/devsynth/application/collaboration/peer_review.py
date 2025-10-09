from __future__ import annotations

"""Peer review utilities for WSDE teams."""

from collections import OrderedDict
from dataclasses import dataclass, replace
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.logger import log_consensus_failure
from devsynth.logging_setup import DevSynthLogger

from .dto import (
    ConsensusOutcome,
    PeerReviewRecord,
    ReviewDecision,
    serialize_collaboration_dto,
)
from .exceptions import ConsensusError, PeerReviewConsensusError
from .message_protocol import MessageType
from .structures import ReviewCycleSpec, ReviewCycleState

logger = DevSynthLogger(__name__)


@dataclass(frozen=True)
class _PeerReviewRecordStorage:
    """Envelope object for persisting peer review records."""

    review_id: str
    record: PeerReviewRecord
    decisions: Tuple[ReviewDecision, ...]
    created_at: datetime
    updated_at: datetime
    quality_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the storage payload deterministically."""

        record_payload = serialize_collaboration_dto(self.record)
        decision_payloads = [
            serialize_collaboration_dto(decision) for decision in self.decisions
        ]
        return OrderedDict(
            [
                ("dto_type", "PeerReviewRecordStorage"),
                ("review_id", self.review_id),
                ("record", record_payload),
                ("decisions", decision_payloads),
                ("quality_score", self.quality_score),
                ("created_at", self.created_at.isoformat()),
                ("updated_at", self.updated_at.isoformat()),
            ]
        )

    def memory_metadata(self) -> Mapping[str, Any]:
        """Metadata used by the memory subsystem."""

        consensus_id = None
        if self.record.consensus is not None:
            consensus_id = getattr(self.record.consensus, "consensus_id", None)

        return OrderedDict(
            [
                ("entity_type", "PeerReviewRecord"),
                ("review_id", self.review_id),
                ("consensus_id", consensus_id),
                ("status", self.record.notes or ""),
                ("quality_score", self.quality_score),
                ("created_at", self.created_at.isoformat()),
                ("updated_at", self.updated_at.isoformat()),
            ]
        )


class PeerReview:
    """Represents a peer review cycle for a work product."""

    def __init__(
        self,
        *,
        cycle: Optional[ReviewCycleSpec] = None,
        work_product: Any | None = None,
        author: Any | None = None,
        reviewers: Optional[Iterable[Any]] = None,
        send_message: Optional[Callable[..., Any]] = None,
        acceptance_criteria: Optional[Iterable[str]] = None,
        quality_metrics: Optional[Mapping[str, Any]] = None,
        team: Optional[Any] = None,
        memory_manager: Optional[MemoryManager] = None,
        previous_review: Optional["PeerReview"] = None,
    ) -> None:
        if cycle is None:
            if reviewers is None:
                raise ValueError(
                    "reviewers must be provided when no ReviewCycleSpec is supplied"
                )
            cycle = ReviewCycleSpec(
                work_product=work_product,
                author=author,
                reviewers=tuple(reviewers),
                send_message=send_message,
                acceptance_criteria=(
                    tuple(acceptance_criteria)
                    if acceptance_criteria is not None
                    else None
                ),
                quality_metrics=(
                    dict(quality_metrics) if quality_metrics is not None else None
                ),
                team=team,
                memory_manager=memory_manager,
            )
        self.cycle: ReviewCycleSpec = cycle
        self._memory_manager: Optional[MemoryManager] = (
            memory_manager or cycle.memory_manager
        )
        self._team: Optional[Any] = cycle.team
        self.reviews: Dict[str, ReviewDecision] = {}
        self.previous_review: Optional["PeerReview"] = previous_review
        self._state: ReviewCycleState = ReviewCycleState()
        self._latest_record: Optional[PeerReviewRecord] = None

    @property
    def review_id(self) -> str:
        return cast(str, self._state.review_id)

    @review_id.setter
    def review_id(self, value: str) -> None:
        self._state.review_id = value
        self._touch()

    @property
    def work_product(self) -> Any:
        return self.cycle.work_product

    @property
    def author(self) -> Any:
        return self.cycle.author

    @property
    def reviewers(self) -> Sequence[Any]:
        return cast(Sequence[Any], self.cycle.reviewers)

    @property
    def send_message(self) -> Optional[Callable[..., Any]]:
        return cast(Optional[Callable[..., Any]], self.cycle.send_message)

    @property
    def acceptance_criteria(self) -> Optional[Sequence[str]]:
        return cast(Optional[Sequence[str]], self.cycle.acceptance_criteria)

    @property
    def quality_metrics(self) -> Optional[Mapping[str, Any]]:
        return cast(Optional[Mapping[str, Any]], self.cycle.quality_metrics)

    @property
    def team(self) -> Optional[Any]:
        return self._team

    @team.setter
    def team(self, value: Optional[Any]) -> None:
        self._team = value
        self.cycle = replace(self.cycle, team=value)

    @property
    def memory_manager(self) -> Optional[MemoryManager]:
        return self._memory_manager

    @memory_manager.setter
    def memory_manager(self, value: Optional[MemoryManager]) -> None:
        self._memory_manager = value

    @property
    def created_at(self) -> datetime:
        return cast(datetime, self._state.created_at)

    @created_at.setter
    def created_at(self, value: datetime) -> None:
        self._state.created_at = value

    @property
    def updated_at(self) -> datetime:
        return cast(datetime, self._state.updated_at)

    @updated_at.setter
    def updated_at(self, value: datetime) -> None:
        self._state.updated_at = value

    def _touch(self) -> None:
        self._state.touch()

    @property
    def status(self) -> str:
        return cast(str, self._state.status)

    @status.setter
    def status(self, value: str) -> None:
        self._state.status = value
        self._touch()

    @property
    def quality_score(self) -> float:
        return cast(float, self._state.quality_score)

    @quality_score.setter
    def quality_score(self, value: float) -> None:
        self._state.quality_score = value
        self._touch()

    @property
    def revision(self) -> Any:
        return self._state.revision

    @revision.setter
    def revision(self, value: Any) -> None:
        self._state.revision = value
        self._touch()

    @property
    def revision_history(self) -> list[Any]:
        return cast(list[Any], self._state.revision_history)

    @property
    def metrics_results(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], self._state.metrics_results)

    @metrics_results.setter
    def metrics_results(self, value: Dict[str, Any]) -> None:
        self._state.metrics_results = value
        self._touch()

    @property
    def consensus_result(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], self._state.consensus_result)

    @consensus_result.setter
    def consensus_result(self, value: Dict[str, Any]) -> None:
        self._state.consensus_result = value
        self._touch()

    @property
    def consensus_outcome(self) -> Optional[ConsensusOutcome]:
        return self._state.consensus_outcome

    @consensus_outcome.setter
    def consensus_outcome(self, value: Optional[ConsensusOutcome]) -> None:
        self._state.consensus_outcome = value
        self._touch()

    def store_in_memory(self, immediate_sync: bool = False) -> Optional[str]:
        """
        Store the review in memory with optional cross-store synchronization.

        Args:
            immediate_sync: Whether to synchronize immediately or queue for later

        Returns:
            The ID of the stored review, or None if storage failed
        """
        if self.memory_manager is None:
            logger.debug("Memory manager not available, skipping storage")
            return None

        try:
            # Import here to avoid circular imports
            from .collaboration_memory_utils import store_with_retry

            storage_payload = self._serialize_for_memory()
            if storage_payload is None:
                logger.debug(
                    "No peer review record available for storage",
                    extra={"review_id": self.review_id},
                )
                return None

            # Determine the primary store to use
            primary_store = self._get_primary_store()

            # Store with retry for better reliability
            item_id: str = store_with_retry(
                self.memory_manager,
                storage_payload,
                primary_store=primary_store,
                immediate_sync=immediate_sync,
                max_retries=3,
            )
            # Ensure queued updates are flushed so data persists
            try:
                self.memory_manager.flush_updates()
            except Exception as flush_error:
                logger.warning(
                    f"Failed to flush memory updates for review {self.review_id}: {flush_error}"
                )
            return item_id
        except Exception as e:
            logger.error(f"Failed to store review {self.review_id} in memory: {str(e)}")
            return None

    def _get_primary_store(self) -> str:
        """
        Determine the primary store to use for this review.

        Returns:
            The name of the primary store
        """
        if self.memory_manager is None:
            return "tinydb"  # Default fallback

        # Try to find the best store in this order: tinydb, graph, kuzu, first available
        if "tinydb" in self.memory_manager.adapters:
            return "tinydb"
        elif "graph" in self.memory_manager.adapters:
            return "graph"
        elif "kuzu" in self.memory_manager.adapters:
            return "kuzu"
        elif self.memory_manager.adapters:
            return cast(str, next(iter(self.memory_manager.adapters)))
        else:
            return "tinydb"  # Default fallback

    def _start_transaction(self) -> Tuple[bool, Any]:
        """
        Start a transaction for atomic operations.

        Returns:
            A tuple of (success, transaction_id)
        """
        if self.memory_manager is None or not hasattr(
            self.memory_manager, "sync_manager"
        ):
            return False, None

        try:
            transaction_id = (
                f"peer_review_{self.review_id}_{datetime.now().timestamp()}"
            )
            self.memory_manager.sync_manager.begin_transaction(transaction_id)
            return True, transaction_id
        except Exception as e:
            logger.error(f"Failed to start transaction: {str(e)}")
            return False, None

    def _commit_transaction(self, transaction_id: Any) -> bool:
        """
        Commit a transaction.

        Args:
            transaction_id: The ID of the transaction to commit

        Returns:
            True if the transaction was committed successfully, False otherwise
        """
        if self.memory_manager is None or not hasattr(
            self.memory_manager, "sync_manager"
        ):
            return False

        try:
            self.memory_manager.sync_manager.commit_transaction(transaction_id)
            return True
        except Exception as e:
            logger.error(f"Failed to commit transaction {transaction_id}: {str(e)}")
            return False

    def _rollback_transaction(self, transaction_id: Any) -> bool:
        """
        Rollback a transaction.

        Args:
            transaction_id: The ID of the transaction to rollback

        Returns:
            True if the transaction was rolled back successfully, False otherwise
        """
        if self.memory_manager is None or not hasattr(
            self.memory_manager, "sync_manager"
        ):
            return False

        try:
            self.memory_manager.sync_manager.rollback_transaction(transaction_id)
            return True
        except Exception as e:
            logger.error(f"Failed to rollback transaction {transaction_id}: {str(e)}")
            return False

    def _reviewer_identifier(self, reviewer: Any) -> str:
        """Return a stable identifier for a reviewer."""

        for attr in ("id", "agent_id"):
            value = getattr(reviewer, attr, None)
            if value:
                return str(value)
        name = getattr(reviewer, "name", None)
        if name:
            return str(name)
        return str(reviewer)

    def _prepare_review_payload(self, raw_result: Any) -> Dict[str, Any]:
        """Normalize reviewer output into a mapping."""

        if isinstance(raw_result, Mapping):
            payload = {str(key): raw_result[key] for key in raw_result.keys()}
        else:
            payload = {"feedback": str(raw_result)}

        if self.acceptance_criteria and "criteria_results" not in payload:
            payload["criteria_results"] = {
                criterion: True for criterion in self.acceptance_criteria
            }

        if self.quality_metrics and "metrics_results" not in payload:
            payload["metrics_results"] = {
                metric: 1.0 for metric in self.quality_metrics
            }

        return payload

    def _build_review_decision(self, reviewer: Any, raw_result: Any) -> ReviewDecision:
        """Construct a :class:`ReviewDecision` from reviewer feedback."""

        reviewer_id = self._reviewer_identifier(reviewer)
        reviewer_name = getattr(reviewer, "name", reviewer_id)

        if isinstance(raw_result, ReviewDecision):
            metadata = (
                OrderedDict(sorted(raw_result.metadata.items()))
                if isinstance(raw_result.metadata, Mapping)
                else OrderedDict()
            )
            decision_id = raw_result.decision_id or f"{self.review_id}:{reviewer_id}"
            return ReviewDecision(
                decision_id=str(decision_id),
                reviewer=raw_result.reviewer or reviewer_name,
                approved=raw_result.approved,
                notes=raw_result.notes,
                score=raw_result.score,
                metadata=metadata,
            )

        payload = self._prepare_review_payload(raw_result)

        decision_id = str(
            payload.get("decision_id") or f"{self.review_id}:{reviewer_id}"
        )
        approved_value = payload.get("approved")
        approved: Optional[bool]
        if isinstance(approved_value, bool) or approved_value is None:
            approved = approved_value
        else:
            approved = None

        notes = payload.get("feedback") or payload.get("notes")
        if notes is not None:
            notes = str(notes)

        score_value = payload.get("score")
        score: Optional[float] = None
        if isinstance(score_value, (int, float)):
            score = float(score_value)
        else:
            metrics = payload.get("metrics_results")
            if isinstance(metrics, Mapping):
                numeric_scores = [
                    float(value)
                    for value in metrics.values()
                    if isinstance(value, (int, float))
                ]
                if numeric_scores:
                    score = sum(numeric_scores) / len(numeric_scores)

        metadata_items = [
            (str(key), payload[key])
            for key in payload.keys()
            if key not in {"decision_id", "approved", "feedback", "notes", "score"}
        ]

        metadata = OrderedDict(sorted(metadata_items, key=lambda item: item[0]))

        return ReviewDecision(
            decision_id=decision_id,
            reviewer=str(reviewer_name),
            approved=approved,
            notes=notes,
            score=score,
            metadata=metadata,
        )

    def _coerce_consensus_outcome(self, result: Any) -> Optional[ConsensusOutcome]:
        """Convert arbitrary consensus payloads into a DTO."""

        if not result:
            return None
        if isinstance(result, ConsensusOutcome):
            return result
        if isinstance(result, Mapping):
            try:
                return ConsensusOutcome.from_dict(result)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug(
                    "Failed to coerce consensus outcome", extra={"error": str(exc)}
                )
                consensus_id = str(result.get("consensus_id", self.review_id))
                task_id = str(result.get("task_id", self.review_id))
                method = str(result.get("method", "unknown"))
                majority = str(result.get("majority_opinion", ""))
                return ConsensusOutcome(
                    consensus_id=consensus_id,
                    task_id=task_id,
                    method=method,
                    agent_opinions=tuple(),
                    majority_opinion=majority,
                )
        return None

    def _build_peer_review_record(
        self, decisions: Iterable[ReviewDecision]
    ) -> PeerReviewRecord:
        """Aggregate the collected decisions into a record DTO."""

        decision_list = tuple(decisions)
        reviewer_names = tuple(
            decision.reviewer or "unknown" for decision in decision_list
        )
        consensus = self.consensus_outcome or self._coerce_consensus_outcome(
            self.consensus_result
        )
        if consensus is not None:
            self.consensus_result = consensus.to_dict()

        summary_notes = "\n".join(
            note
            for note in (decision.notes or "" for decision in decision_list)
            if note
        )

        aggregate_metadata = OrderedDict(
            [
                ("review_id", self.review_id),
                ("status", self.status),
                ("created_at", self.created_at.isoformat()),
                ("updated_at", self.updated_at.isoformat()),
                ("quality_score", self.quality_score),
                ("review_count", len(decision_list)),
            ]
        )

        if self.acceptance_criteria:
            aggregate_metadata["acceptance_criteria"] = tuple(self.acceptance_criteria)
        if self.quality_metrics:
            aggregate_metadata["quality_metrics"] = OrderedDict(
                sorted((str(k), v) for k, v in self.quality_metrics.items())
            )

        aggregate_metadata["decisions"] = [
            serialize_collaboration_dto(decision) for decision in decision_list
        ]

        summary_decision = ReviewDecision(
            decision_id=f"{self.review_id}:aggregate",
            reviewer="peer_review",
            approved=self.status == "approved",
            notes=summary_notes or None,
            score=self.quality_score if self.quality_score else None,
            metadata=aggregate_metadata,
        )

        return PeerReviewRecord(
            task=None,
            decision=summary_decision,
            consensus=consensus,
            reviewers=reviewer_names,
            notes=self.status,
            metadata=aggregate_metadata,
        )

    def _serialize_for_memory(self) -> Optional[_PeerReviewRecordStorage]:
        """Build the storage envelope for persistence."""

        decisions = tuple(self.reviews.values())
        record = self._latest_record or self._build_peer_review_record(decisions)
        self._latest_record = record
        return _PeerReviewRecordStorage(
            review_id=self.review_id,
            record=record,
            decisions=decisions,
            created_at=self.created_at,
            updated_at=self.updated_at,
            quality_score=self.quality_score,
        )

    def assign_reviews(self) -> None:
        """Notify reviewers of the review request."""
        self._touch()

        # Start a transaction for atomic operations
        transaction_started, transaction_id = self._start_transaction()

        try:
            if self.team and hasattr(self.team, "select_primus_by_expertise"):
                task_context = {
                    "type": "peer_review",
                    "description": getattr(self.work_product, "description", ""),
                }
                try:
                    self.team.select_primus_by_expertise(task_context)
                    if hasattr(self.team, "rotate_roles"):
                        self.team.rotate_roles()
                except Exception as e:
                    logger.warning(
                        f"Error selecting primus or rotating roles: {str(e)}"
                    )

            if self.send_message:
                for reviewer in self.reviewers:
                    content = {
                        "work_product": self.work_product,
                        "review_id": self.review_id,
                    }

                    if self.acceptance_criteria:
                        content["acceptance_criteria"] = self.acceptance_criteria

                    if self.quality_metrics:
                        content["quality_metrics"] = self.quality_metrics

                    self.send_message(
                        sender=getattr(self.author, "name", str(self.author)),
                        recipients=[getattr(reviewer, "name", str(reviewer))],
                        message_type=MessageType.REVIEW_REQUEST,
                        subject="Peer Review Request",
                        content=content,
                    )

            # Store the review in memory
            self.store_in_memory(immediate_sync=transaction_started)

            # Commit the transaction if it was started
            if transaction_started:
                self._commit_transaction(transaction_id)

        except Exception as e:
            logger.error(f"Error in assign_reviews: {str(e)}")
            # Rollback the transaction if it was started
            if transaction_started:
                self._rollback_transaction(transaction_id)

    def collect_reviews(self) -> Dict[str, ReviewDecision]:
        """Gather feedback from all reviewers."""

        self._touch()

        # Start a transaction for atomic operations
        transaction_started, transaction_id = self._start_transaction()

        try:
            task_context = {"id": self.review_id, "type": "peer_review"}
            if self.team and hasattr(self.team, "rotate_roles"):
                try:
                    self.team.rotate_roles()
                except Exception as e:
                    logger.warning(f"Error rotating roles: {str(e)}")

            for reviewer in self.reviewers:
                if hasattr(reviewer, "process"):
                    process_input = {
                        "work_product": self.work_product,
                        "review_id": self.review_id,
                    }

                    if self.acceptance_criteria:
                        process_input["acceptance_criteria"] = self.acceptance_criteria

                    if self.quality_metrics:
                        process_input["quality_metrics"] = self.quality_metrics

                    # Check if this is a critic agent that should perform dialectical analysis
                    is_critic = False
                    if hasattr(reviewer, "config") and hasattr(
                        reviewer.config, "agent_type"
                    ):
                        is_critic = reviewer.config.agent_type.name == "CRITIC"
                    elif hasattr(reviewer, "expertise") and reviewer.expertise:
                        is_critic = any(
                            exp.lower() in ["critic", "dialectical", "critique"]
                            for exp in reviewer.expertise
                        )

                    # If this is a critic, prepare for dialectical analysis
                    if is_critic:
                        process_input["task"] = "perform_dialectical_critique"
                        process_input["critique_aspects"] = [
                            "security",
                            "performance",
                            "maintainability",
                            "readability",
                            "error_handling",
                            "input_validation",
                        ]
                        process_input["format"] = "structured"

                    try:
                        result = reviewer.process(process_input)
                    except Exception as e:
                        logger.error(f"Error processing review by {reviewer}: {str(e)}")
                        result = {"feedback": f"Error processing review: {str(e)}"}

                    # If this is a critic, enhance the result with dialectical analysis
                    if is_critic and "code" in self.work_product:
                        # Create a task and solution for dialectical reasoning
                        task = {
                            "type": "review_task",
                            "description": "Review the provided code or content",
                        }

                        solution = {
                            "agent": getattr(self.author, "name", str(self.author)),
                            "content": self.work_product.get("description", ""),
                            "code": self.work_product.get("code", ""),
                        }

                        # Try to use WSDETeam's dialectical reasoning if available
                        try:
                            from devsynth.domain.models.wsde_facade import WSDETeam

                            temp_team = WSDETeam(name="PeerReviewTeam")
                            temp_team.add_solution(task, solution)

                            dialectical_result = temp_team.apply_dialectical_reasoning(
                                task, reviewer
                            )

                            # Add dialectical analysis to the result
                            if (
                                "thesis" in dialectical_result
                                and "antithesis" in dialectical_result
                                and "synthesis" in dialectical_result
                            ):
                                result["thesis"] = dialectical_result["thesis"].get(
                                    "content",
                                    "The solution provides basic functionality.",
                                )
                                result["antithesis"] = dialectical_result[
                                    "antithesis"
                                ].get("critique", ["The solution could be improved."])
                                result["synthesis"] = dialectical_result[
                                    "synthesis"
                                ].get(
                                    "improved_solution",
                                    "Improved implementation recommended.",
                                )

                                # Add dialectical analysis as a structured object
                                result["dialectical_analysis"] = {
                                    "thesis": {
                                        "content": dialectical_result["thesis"].get(
                                            "content", ""
                                        ),
                                        "strengths": ["Provides basic functionality"],
                                    },
                                    "antithesis": {
                                        "critique": dialectical_result[
                                            "antithesis"
                                        ].get("critique", []),
                                        "challenges": dialectical_result[
                                            "antithesis"
                                        ].get("challenges", []),
                                    },
                                    "synthesis": {
                                        "improvements": dialectical_result[
                                            "synthesis"
                                        ].get("improvements", []),
                                        "improved_solution": dialectical_result[
                                            "synthesis"
                                        ].get("improved_solution", ""),
                                    },
                                }
                        except (ImportError, Exception) as e:
                            logger.warning(
                                f"Error applying dialectical reasoning: {str(e)}"
                            )
                            # If WSDETeam is not available or fails, create a simple dialectical analysis
                            if "thesis" not in result:
                                result["thesis"] = (
                                    "The solution provides basic functionality."
                                )
                            if "antithesis" not in result:
                                result["antithesis"] = (
                                    "The solution could be improved in several ways."
                                )
                            if "synthesis" not in result:
                                result["synthesis"] = (
                                    "An improved implementation would address the identified issues."
                                )
                else:
                    result = {"feedback": "ok"}

                decision = self._build_review_decision(reviewer, result)
                reviewer_key = self._reviewer_identifier(reviewer)
                self.reviews[reviewer_key] = decision

                if self.team and hasattr(self.team, "add_solution"):
                    try:
                        sol = {
                            "agent": getattr(reviewer, "name", str(reviewer)),
                            "content": decision.notes or "",
                        }
                        self.team.add_solution(task_context, sol)
                    except Exception as e:
                        logger.warning(f"Error adding solution to team: {str(e)}")

            # Calculate quality score if metrics are available
            self._calculate_quality_score()

            if self.team and hasattr(self.team, "build_consensus"):
                try:
                    consensus_raw = self.team.build_consensus(task_context)
                    outcome = self._coerce_consensus_outcome(consensus_raw)
                    if outcome is None:
                        raise PeerReviewConsensusError(
                            "Consensus not reached",
                            outcome=None,
                            review_id=self.review_id,
                        )
                    self.consensus_outcome = outcome
                    self.consensus_result = outcome.to_dict()
                except PeerReviewConsensusError as exc:
                    log_consensus_failure(
                        logger,
                        exc,
                        extra={
                            "review_id": self.review_id,
                            "consensus_id": getattr(exc.outcome, "consensus_id", None),
                        },
                    )
                    self.consensus_outcome = exc.outcome
                    if exc.outcome is None:
                        self.consensus_result = {}
                    else:
                        self.consensus_result = exc.outcome.to_dict()
                except ConsensusError as exc:
                    raw_consensus = getattr(exc, "consensus_result", None)
                    wrapped = PeerReviewConsensusError(
                        str(exc),
                        outcome=self._coerce_consensus_outcome(raw_consensus),
                        review_id=self.review_id,
                        consensus_payload=(
                            dict(raw_consensus)
                            if isinstance(raw_consensus, Mapping)
                            else None
                        ),
                    )
                    log_consensus_failure(
                        logger,
                        wrapped,
                        extra={
                            "review_id": self.review_id,
                            "consensus_id": getattr(
                                wrapped.outcome, "consensus_id", None
                            ),
                        },
                    )
                    self.consensus_outcome = wrapped.outcome
                    if wrapped.outcome is None:
                        self.consensus_result = {}
                    else:
                        self.consensus_result = wrapped.outcome.to_dict()
                    if self.consensus_outcome is None and self.consensus_result:
                        self.consensus_outcome = self._coerce_consensus_outcome(
                            self.consensus_result
                        )
                except Exception as e:
                    logger.warning(f"Error building consensus: {str(e)}")
                    self.consensus_result = {}

            # Store the updated review in memory
            self.store_in_memory(immediate_sync=transaction_started)

            # Commit the transaction if it was started
            if transaction_started:
                self._commit_transaction(transaction_id)

            return self.reviews

        except Exception as e:
            logger.error(f"Error in collect_reviews: {str(e)}")
            # Rollback the transaction if it was started
            if transaction_started:
                self._rollback_transaction(transaction_id)
            return self.reviews

    def _calculate_quality_score(self) -> None:
        """Calculate the overall quality score based on metrics results."""
        if not self.quality_metrics or not self.reviews:
            self.quality_score = 0.0
            return

        total_score = 0.0
        total_metrics = 0

        for decision in self.reviews.values():
            metrics = decision.metadata.get("metrics_results")
            if isinstance(metrics, Mapping):
                for metric, score in metrics.items():
                    if isinstance(score, (int, float)):
                        score_value = float(score)
                        total_score += score_value
                        total_metrics += 1

                        if metric not in self.metrics_results:
                            self.metrics_results[metric] = []
                        self.metrics_results[metric].append(score_value)

        # Calculate average score
        self.quality_score = total_score / total_metrics if total_metrics > 0 else 0.0

        # Calculate average for each metric
        for metric, scores in self.metrics_results.items():
            self.metrics_results[metric] = sum(scores) / len(scores)

        if self.metrics_results:
            self._touch()

    def aggregate_feedback(self) -> Dict[str, Any]:
        """Aggregate feedback from reviewers into a single structure."""

        self._touch()

        decisions = tuple(self.reviews.values())
        record = self._build_peer_review_record(decisions)
        self._latest_record = record

        feedback_notes = [decision.notes or "" for decision in decisions]

        result: Dict[str, Any] = {
            "feedback": feedback_notes,
            "quality_score": self.quality_score,
            "review_id": self.review_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "peer_review_record": serialize_collaboration_dto(record),
            "decisions": [serialize_collaboration_dto(d) for d in decisions],
        }

        if self.acceptance_criteria:
            criteria_votes: Dict[str, List[bool]] = {}
            for decision in decisions:
                criteria = decision.metadata.get("criteria_results")
                if isinstance(criteria, Mapping):
                    for criterion, passed in criteria.items():
                        votes = criteria_votes.setdefault(str(criterion), [])
                        votes.append(bool(passed))

            final_criteria: Dict[str, bool] = {}
            for criterion, votes in criteria_votes.items():
                final_criteria[criterion] = (
                    sum(1 for vote in votes if vote) > len(votes) / 2
                )

            result["criteria_results"] = final_criteria
            result["all_criteria_passed"] = (
                all(final_criteria.values()) if final_criteria else True
            )

        if self.metrics_results:
            result["metrics_results"] = self.metrics_results

        dialectical_analysis: Dict[str, Any] = {}
        for decision in decisions:
            metadata = decision.metadata
            for key in ("thesis", "antithesis", "synthesis"):
                if key in metadata:
                    dialectical_analysis[key] = metadata[key]
            if "dialectical_analysis" in metadata:
                result["dialectical_analysis"] = metadata["dialectical_analysis"]
                break

        if dialectical_analysis and "dialectical_analysis" not in result:
            result["dialectical_analysis"] = dialectical_analysis

        if self.consensus_result:
            result["consensus"] = self.consensus_result

        return result

    def request_revision(self) -> None:
        """Mark the review as requiring revision."""

        self._touch()
        self.status = "revision_requested"

        # Start a transaction for atomic operations
        transaction_started, transaction_id = self._start_transaction()

        try:
            # Store the updated review in memory
            self.store_in_memory(immediate_sync=transaction_started)

            # Commit the transaction if it was started
            if transaction_started:
                self._commit_transaction(transaction_id)

        except Exception as e:
            logger.error(f"Error in request_revision: {str(e)}")
            # Rollback the transaction if it was started
            if transaction_started:
                self._rollback_transaction(transaction_id)

    def submit_revision(self, revision: Any) -> "PeerReview":
        """
        Submit a revised work product for further review.

        Returns:
            A new PeerReview instance linked to this one.
        """
        self._touch()
        self.revision = revision
        self.revision_history.append(revision)
        self._touch()
        self.status = "revised"

        # Start a transaction for atomic operations
        transaction_started, transaction_id = self._start_transaction()

        try:
            # Store the updated review in memory
            self.store_in_memory(immediate_sync=transaction_started)

            # Create a new review for the revision, linked to this one
            new_review = PeerReview(
                work_product=revision,
                author=self.author,
                reviewers=self.reviewers,
                send_message=self.send_message,
                acceptance_criteria=self.acceptance_criteria,
                quality_metrics=self.quality_metrics,
                team=self.team,
                memory_manager=self.memory_manager,  # Pass the memory manager to the new review
                previous_review=self,
            )

            # Store the new review in memory
            new_review.store_in_memory(immediate_sync=transaction_started)

            # Commit the transaction if it was started
            if transaction_started:
                self._commit_transaction(transaction_id)

            return new_review

        except Exception as e:
            logger.error(f"Error in submit_revision: {str(e)}")
            # Rollback the transaction if it was started
            if transaction_started:
                self._rollback_transaction(transaction_id)

            # Create a new review without memory integration as fallback
            new_review = PeerReview(
                work_product=revision,
                author=self.author,
                reviewers=self.reviewers,
                send_message=self.send_message,
                acceptance_criteria=self.acceptance_criteria,
                quality_metrics=self.quality_metrics,
                team=self.team,
                previous_review=self,
            )

            return new_review

    def finalize(self, approved: bool = True) -> Dict[str, Any]:
        """Finalize the peer review and return aggregated feedback."""

        self._touch()
        self.status = "approved" if approved else "rejected"

        # Start a transaction for atomic operations
        transaction_started, transaction_id = self._start_transaction()

        try:
            # Determine if all criteria passed (if applicable)
            all_criteria_passed = True
            if self.acceptance_criteria:
                feedback = self.aggregate_feedback()
                all_criteria_passed = feedback.get("all_criteria_passed", False)

                # Override approval if criteria failed
                if not all_criteria_passed and approved:
                    self.status = "rejected"
                    approved = False

            # Check quality score against a threshold
            quality_threshold = 0.7  # Configurable threshold
            if (
                hasattr(self, "quality_score")
                and self.quality_score < quality_threshold
                and approved
            ):
                # If quality score is low but no revision was requested yet,
                # suggest revision instead of rejection
                if self.status != "revision_requested" and not self.revision:
                    self.status = "revision_suggested"
                # If quality is still low after revision, reject
                elif self.revision:
                    self.status = "rejected"
                    approved = False

            feedback = self.aggregate_feedback()  # Regenerate with updated status

            result = {
                "status": self.status,
                "feedback": feedback,
                "quality_score": self.quality_score,
                "approved": approved,
                "review_id": self.review_id,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
            }

            # Add reasons for rejection if applicable
            if self.status == "rejected" and self.acceptance_criteria:
                criteria_results = feedback.get("criteria_results", {})
                reasons = [
                    f"{criterion}: Failed"
                    for criterion, passed in criteria_results.items()
                    if not passed
                ]
                result["reasons"] = reasons

            # Include revision history
            if self.revision_history:
                result["revisions"] = {
                    "count": len(self.revision_history),
                    "history": self.revision_history,
                }

            # Include previous review reference
            if self.previous_review:
                result["previous_review_id"] = self.previous_review.review_id

                # Include a summary of the revision chain
                revision_chain = []
                current_review = self
                while current_review.previous_review:
                    revision_chain.append(
                        {
                            "review_id": current_review.previous_review.review_id,
                            "status": current_review.previous_review.status,
                            "quality_score": current_review.previous_review.quality_score,
                        }
                    )
                    current_review = current_review.previous_review

                if revision_chain:
                    result["revision_chain"] = revision_chain

            # Add dialectical analysis if available in the feedback
            if isinstance(feedback, dict) and "dialectical_analysis" in feedback:
                result["dialectical_analysis"] = feedback["dialectical_analysis"]

            if self.consensus_result:
                result["consensus"] = self.consensus_result

            # Store the finalized review in memory
            self.store_in_memory(immediate_sync=transaction_started)

            # Commit the transaction if it was started
            if transaction_started:
                self._commit_transaction(transaction_id)

            return result

        except Exception as e:
            logger.error(f"Error in finalize: {str(e)}")
            # Rollback the transaction if it was started
            if transaction_started:
                self._rollback_transaction(transaction_id)

            # Create a minimal result as fallback
            return {
                "status": self.status,
                "approved": approved,
                "review_id": self.review_id,
                "error": f"Error finalizing review: {str(e)}",
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
            }


@dataclass
class PeerReviewWorkflow:
    """Encapsulates a full peer review workflow."""

    work_product: Any
    author: Any
    reviewers: List[Any]
    send_message: Optional[Callable[..., Any]] = None
    acceptance_criteria: Optional[List[str]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    max_revision_cycles: int = 3
    team: Optional[Any] = None
    memory_manager: Optional[MemoryManager] = None

    def _get_revision_from_author(
        self, revision_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get a revised version of the work from the author based on feedback.

        Args:
            revision_request: A dictionary containing the original work, feedback summary,
                             improvement suggestions, and other relevant information

        Returns:
            A dictionary containing the revised work
        """
        logger.info(
            f"Requesting revision from author: {getattr(self.author, 'name', 'Unknown')}"
        )

        # If the author has a revise_work method, use it
        if hasattr(self.author, "revise_work") and callable(
            getattr(self.author, "revise_work")
        ):
            try:
                revised_work = self.author.revise_work(revision_request)
                if revised_work:
                    logger.info("Author provided revision using revise_work method")
                    return cast(Dict[str, Any], revised_work)
            except Exception as e:
                logger.error(
                    f"Error getting revision from author's revise_work method: {str(e)}"
                )

        # If the team has a request_revision method, use it
        if (
            self.team
            and hasattr(self.team, "request_revision")
            and callable(getattr(self.team, "request_revision"))
        ):
            try:
                revised_work = self.team.request_revision(self.author, revision_request)
                if revised_work:
                    logger.info("Team provided revision using request_revision method")
                    return cast(Dict[str, Any], revised_work)
            except Exception as e:
                logger.error(
                    f"Error getting revision from team's request_revision method: {str(e)}"
                )

        # If the author has a generate_response method (UnifiedAgent interface), use it
        if hasattr(self.author, "generate_response") and callable(
            getattr(self.author, "generate_response")
        ):
            try:
                # Prepare a prompt for the author
                prompt = f"""
                You need to revise your work based on the following feedback:

                ORIGINAL WORK:
                {revision_request.get('original_work', {})}

                FEEDBACK SUMMARY:
                {revision_request.get('feedback_summary', 'No summary provided')}

                IMPROVEMENT SUGGESTIONS:
                {', '.join(revision_request.get('improvement_suggestions', ['No suggestions provided']))}

                Please provide a revised version that addresses this feedback.
                """

                response = self.author.generate_response(prompt)
                if response:
                    logger.info(
                        "Author provided revision using generate_response method"
                    )
                    return {
                        "original": revision_request.get("original_work", {}),
                        "revision": response,
                        "revision_number": revision_request.get("revision_number", 1),
                        "improvements": "Addressed reviewer feedback",
                    }
            except Exception as e:
                logger.error(
                    f"Error getting revision from author's generate_response method: {str(e)}"
                )

        # If all else fails, create a simulated revision (fallback for compatibility)
        logger.warning(
            "Could not get actual revision from author, using simulated revision"
        )
        return {
            "original": revision_request.get("original_work", {}),
            "revision": f"Revision {revision_request.get('revision_number', 1)}",
            "revision_number": revision_request.get("revision_number", 1),
            "improvements": "Addressed reviewer feedback (simulated)",
            "is_simulated": True,
        }

    def run(self) -> Dict[str, Any]:
        """
        Run a complete peer review workflow with support for revision cycles.

        Returns:
            Dict containing the final review results.
        """
        # Start a transaction for the entire workflow if memory manager is available
        transaction_started = False
        transaction_id = None

        if self.memory_manager is not None and hasattr(
            self.memory_manager, "sync_manager"
        ):
            try:
                transaction_id = f"peer_review_workflow_{datetime.now().timestamp()}"
                self.memory_manager.sync_manager.begin_transaction(transaction_id)
                transaction_started = True
                logger.debug(
                    f"Started transaction {transaction_id} for peer review workflow"
                )
            except Exception as e:
                logger.error(f"Failed to start transaction for workflow: {str(e)}")

        try:
            review = PeerReview(
                work_product=self.work_product,
                author=self.author,
                reviewers=self.reviewers,
                send_message=self.send_message,
                acceptance_criteria=self.acceptance_criteria,
                quality_metrics=self.quality_metrics,
                team=self.team,
                memory_manager=self.memory_manager,
            )

            review.assign_reviews()
            review.collect_reviews()

            # Check if revision is needed
            feedback = review.aggregate_feedback()
            all_criteria_passed = feedback.get("all_criteria_passed", True)
            quality_score = feedback.get("quality_score", 0.0)

            revision_count = 0
            current_review = review

            # Continue revision cycles until criteria pass or max cycles reached
            while (
                not all_criteria_passed or quality_score < 0.7
            ) and revision_count < self.max_revision_cycles:
                current_review.request_revision()

                # Request a revision from the author based on the feedback
                feedback_summary = feedback.get("summary", "")
                improvement_suggestions = feedback.get("improvement_suggestions", [])

                # Prepare the revision request with detailed feedback
                revision_request = {
                    "original_work": current_review.work_product,
                    "feedback_summary": feedback_summary,
                    "improvement_suggestions": improvement_suggestions,
                    "revision_number": revision_count + 1,
                    "criteria_results": feedback.get("criteria_results", {}),
                    "quality_scores": feedback.get("quality_scores", {}),
                }

                # Get the revised work from the author
                revised_work = self._get_revision_from_author(revision_request)

                # Create a new review for the revision
                current_review = current_review.submit_revision(revised_work)
                current_review.assign_reviews()
                current_review.collect_reviews()

                # Check if the revision passes
                feedback = current_review.aggregate_feedback()
                all_criteria_passed = feedback.get("all_criteria_passed", True)
                quality_score = feedback.get("quality_score", 0.0)

                revision_count += 1

            # Finalize with approval based on criteria and quality
            approved = all_criteria_passed and quality_score >= 0.7
            result = current_review.finalize(approved=approved)

            # Add workflow metadata
            result["workflow"] = {
                "revision_cycles": revision_count,
                "max_revision_cycles": self.max_revision_cycles,
                "final_quality_score": quality_score,
                "all_criteria_passed": all_criteria_passed,
            }

            # Commit the transaction if it was started
            if transaction_started and self.memory_manager is not None:
                try:
                    self.memory_manager.sync_manager.commit_transaction(transaction_id)
                    logger.debug(
                        f"Committed transaction {transaction_id} for peer review workflow"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to commit transaction {transaction_id}: {str(e)}"
                    )
                    # We don't rollback here since individual operations may have succeeded
            # Flush any pending memory updates to ensure persistence
            if self.memory_manager is not None:
                try:
                    self.memory_manager.flush_updates()
                except Exception as flush_error:
                    logger.warning(
                        f"Failed to flush memory updates for workflow: {flush_error}"
                    )

            return result

        except Exception as e:
            logger.error(f"Error in peer review workflow: {str(e)}")

            # Rollback the transaction if it was started
            if transaction_started and self.memory_manager is not None:
                try:
                    self.memory_manager.sync_manager.rollback_transaction(
                        transaction_id
                    )
                    logger.debug(
                        f"Rolled back transaction {transaction_id} due to error"
                    )
                except Exception as rollback_error:
                    logger.error(
                        f"Failed to rollback transaction {transaction_id}: {str(rollback_error)}"
                    )

            # Return error information
            return {
                "error": f"Error in peer review workflow: {str(e)}",
                "workflow_status": "failed",
            }


def run_peer_review(
    work_product: Any,
    author: Any,
    reviewers: List[Any],
    send_message: Optional[Callable[..., Any]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    quality_metrics: Optional[Dict[str, Any]] = None,
    max_revision_cycles: int = 3,
    team: Optional[Any] = None,
    memory_manager: Optional[MemoryManager] = None,
) -> Dict[str, Any]:
    """
    Convenience function to execute a full peer review with quality metrics.

    Args:
        work_product: The work to be reviewed
        author: The creator of the work
        reviewers: List of agents who will review the work
        send_message: Optional function to send messages between agents
        acceptance_criteria: Optional list of criteria the work must meet
        quality_metrics: Optional dictionary of quality metrics to evaluate
        max_revision_cycles: Maximum number of revision cycles allowed
        team: Optional WSDETeam for consensus building and role management
        memory_manager: Optional memory manager for persistent storage and cross-store synchronization

    Returns:
        Dict containing the final review results
    """
    try:
        workflow = PeerReviewWorkflow(
            work_product=work_product,
            author=author,
            reviewers=reviewers,
            send_message=send_message,
            acceptance_criteria=acceptance_criteria,
            quality_metrics=quality_metrics,
            max_revision_cycles=max_revision_cycles,
            team=team,
            memory_manager=memory_manager,
        )

        return workflow.run()
    except Exception as e:
        logger.error(f"Error in run_peer_review: {str(e)}")
        return {
            "error": f"Error in run_peer_review: {str(e)}",
            "workflow_status": "failed",
        }
