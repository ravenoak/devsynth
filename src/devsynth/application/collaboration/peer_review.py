from __future__ import annotations

"""Peer review utilities for WSDE teams."""

from typing import Any, Dict, List, Callable, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from .message_protocol import MessageType
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class PeerReview:
    """Represents a peer review cycle for a work product."""

    work_product: Any
    author: Any
    reviewers: List[Any]
    send_message: Optional[Callable[..., Any]] = None
    acceptance_criteria: Optional[List[str]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    team: Optional[Any] = None
    memory_manager: Optional[MemoryManager] = None

    reviews: Dict[Any, Dict[str, Any]] = field(default_factory=dict)
    revision: Any = None
    revision_history: List[Any] = field(default_factory=list)
    status: str = "pending"
    review_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    previous_review: Optional["PeerReview"] = None
    quality_score: float = 0.0
    metrics_results: Dict[str, Any] = field(default_factory=dict)
    consensus_result: Dict[str, Any] = field(default_factory=dict)
    
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
            
            # Determine the primary store to use
            primary_store = self._get_primary_store()
            
            # Store with retry for better reliability
            return store_with_retry(
                self.memory_manager,
                self,
                primary_store=primary_store,
                immediate_sync=immediate_sync,
                max_retries=3
            )
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
            return next(iter(self.memory_manager.adapters))
        else:
            return "tinydb"  # Default fallback
            
    def _start_transaction(self) -> Tuple[bool, Any]:
        """
        Start a transaction for atomic operations.
        
        Returns:
            A tuple of (success, transaction_id)
        """
        if self.memory_manager is None or not hasattr(self.memory_manager, "sync_manager"):
            return False, None
            
        try:
            transaction_id = f"peer_review_{self.review_id}_{datetime.now().timestamp()}"
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
        if self.memory_manager is None or not hasattr(self.memory_manager, "sync_manager"):
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
        if self.memory_manager is None or not hasattr(self.memory_manager, "sync_manager"):
            return False
            
        try:
            self.memory_manager.sync_manager.rollback_transaction(transaction_id)
            return True
        except Exception as e:
            logger.error(f"Failed to rollback transaction {transaction_id}: {str(e)}")
            return False

    def assign_reviews(self) -> None:
        """Notify reviewers of the review request."""
        self.updated_at = datetime.now()
        
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
                    logger.warning(f"Error selecting primus or rotating roles: {str(e)}")

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

    def collect_reviews(self) -> Dict[Any, Dict[str, Any]]:
        """Gather feedback from all reviewers."""

        self.updated_at = datetime.now()
        
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
                            from devsynth.domain.models.wsde import WSDETeam

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
                                    "content", "The solution provides basic functionality."
                                )
                                result["antithesis"] = dialectical_result["antithesis"].get(
                                    "critique", ["The solution could be improved."]
                                )
                                result["synthesis"] = dialectical_result["synthesis"].get(
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
                                        "critique": dialectical_result["antithesis"].get(
                                            "critique", []
                                        ),
                                        "challenges": dialectical_result["antithesis"].get(
                                            "challenges", []
                                        ),
                                    },
                                    "synthesis": {
                                        "improvements": dialectical_result["synthesis"].get(
                                            "improvements", []
                                        ),
                                        "improved_solution": dialectical_result[
                                            "synthesis"
                                        ].get("improved_solution", ""),
                                    },
                                }
                        except (ImportError, Exception) as e:
                            logger.warning(f"Error applying dialectical reasoning: {str(e)}")
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

                # Process criteria results if provided
                if self.acceptance_criteria and "criteria_results" not in result:
                    # Initialize default criteria results if not provided by reviewer
                    result["criteria_results"] = {
                        criterion: True for criterion in self.acceptance_criteria
                    }

                # Process quality metrics if provided
                if self.quality_metrics and "metrics_results" not in result:
                    # Initialize default metrics results if not provided by reviewer
                    result["metrics_results"] = {
                        metric: 1.0 for metric in self.quality_metrics
                    }

                self.reviews[reviewer] = result

                if self.team and hasattr(self.team, "add_solution"):
                    try:
                        sol = {
                            "agent": getattr(reviewer, "name", str(reviewer)),
                            "content": result.get("feedback", ""),
                        }
                        self.team.add_solution(task_context, sol)
                    except Exception as e:
                        logger.warning(f"Error adding solution to team: {str(e)}")

            # Calculate quality score if metrics are available
            self._calculate_quality_score()

            if self.team and hasattr(self.team, "build_consensus"):
                try:
                    self.consensus_result = self.team.build_consensus(task_context)
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

        for review in self.reviews.values():
            if "metrics_results" in review:
                for metric, score in review["metrics_results"].items():
                    if isinstance(score, (int, float)):
                        total_score += float(score)
                        total_metrics += 1

                        # Store individual metric results
                        if metric not in self.metrics_results:
                            self.metrics_results[metric] = []
                        self.metrics_results[metric].append(score)

        # Calculate average score
        self.quality_score = total_score / total_metrics if total_metrics > 0 else 0.0

        # Calculate average for each metric
        for metric, scores in self.metrics_results.items():
            self.metrics_results[metric] = sum(scores) / len(scores)

    def aggregate_feedback(self) -> Dict[str, Any]:
        """Aggregate feedback from reviewers into a single structure."""

        self.updated_at = datetime.now()

        # Collect textual feedback
        feedback = [r.get("feedback", "") for r in self.reviews.values()]

        # Prepare result dictionary
        result = {
            "feedback": feedback,
            "quality_score": self.quality_score,
            "review_id": self.review_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        # Add criteria results if available
        if self.acceptance_criteria:
            criteria_results = {}
            for review in self.reviews.values():
                if "criteria_results" in review:
                    for criterion, passed in review["criteria_results"].items():
                        if criterion not in criteria_results:
                            criteria_results[criterion] = []
                        criteria_results[criterion].append(passed)

            # Determine final pass/fail for each criterion (majority vote)
            final_criteria = {}
            for criterion, results in criteria_results.items():
                final_criteria[criterion] = (
                    sum(1 for r in results if r) > len(results) / 2
                )

            result["criteria_results"] = final_criteria
            result["all_criteria_passed"] = all(final_criteria.values())

        # Add metrics results if available
        if self.metrics_results:
            result["metrics_results"] = self.metrics_results

        # Add dialectical analysis if available
        dialectical_analysis = {}
        for review in self.reviews.values():
            # Check for direct keys
            for key in ["thesis", "antithesis", "synthesis"]:
                if key in review:
                    dialectical_analysis[key] = review[key]

            # Check for nested dialectical_analysis
            if "dialectical_analysis" in review:
                result["dialectical_analysis"] = review["dialectical_analysis"]
                break

        # If we found direct keys but not a nested structure
        if dialectical_analysis and "dialectical_analysis" not in result:
            result["dialectical_analysis"] = dialectical_analysis

        if self.consensus_result:
            result["consensus"] = self.consensus_result

        return result

    def request_revision(self) -> None:
        """Mark the review as requiring revision."""

        self.updated_at = datetime.now()
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
        self.updated_at = datetime.now()
        self.revision = revision
        self.revision_history.append(revision)
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

        self.updated_at = datetime.now()
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
    
    def _get_revision_from_author(self, revision_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a revised version of the work from the author based on feedback.
        
        Args:
            revision_request: A dictionary containing the original work, feedback summary,
                             improvement suggestions, and other relevant information
                             
        Returns:
            A dictionary containing the revised work
        """
        logger.info(f"Requesting revision from author: {getattr(self.author, 'name', 'Unknown')}")
        
        # If the author has a revise_work method, use it
        if hasattr(self.author, "revise_work") and callable(getattr(self.author, "revise_work")):
            try:
                revised_work = self.author.revise_work(revision_request)
                if revised_work:
                    logger.info("Author provided revision using revise_work method")
                    return revised_work
            except Exception as e:
                logger.error(f"Error getting revision from author's revise_work method: {str(e)}")
        
        # If the team has a request_revision method, use it
        if self.team and hasattr(self.team, "request_revision") and callable(getattr(self.team, "request_revision")):
            try:
                revised_work = self.team.request_revision(self.author, revision_request)
                if revised_work:
                    logger.info("Team provided revision using request_revision method")
                    return revised_work
            except Exception as e:
                logger.error(f"Error getting revision from team's request_revision method: {str(e)}")
        
        # If the author has a generate_response method (UnifiedAgent interface), use it
        if hasattr(self.author, "generate_response") and callable(getattr(self.author, "generate_response")):
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
                    logger.info("Author provided revision using generate_response method")
                    return {
                        "original": revision_request.get("original_work", {}),
                        "revision": response,
                        "revision_number": revision_request.get("revision_number", 1),
                        "improvements": "Addressed reviewer feedback"
                    }
            except Exception as e:
                logger.error(f"Error getting revision from author's generate_response method: {str(e)}")
        
        # If all else fails, create a simulated revision (fallback for compatibility)
        logger.warning("Could not get actual revision from author, using simulated revision")
        return {
            "original": revision_request.get("original_work", {}),
            "revision": f"Revision {revision_request.get('revision_number', 1)}",
            "revision_number": revision_request.get("revision_number", 1),
            "improvements": "Addressed reviewer feedback (simulated)",
            "is_simulated": True
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
        
        if self.memory_manager is not None and hasattr(self.memory_manager, "sync_manager"):
            try:
                transaction_id = f"peer_review_workflow_{datetime.now().timestamp()}"
                self.memory_manager.sync_manager.begin_transaction(transaction_id)
                transaction_started = True
                logger.debug(f"Started transaction {transaction_id} for peer review workflow")
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
            if transaction_started:
                try:
                    self.memory_manager.sync_manager.commit_transaction(transaction_id)
                    logger.debug(f"Committed transaction {transaction_id} for peer review workflow")
                except Exception as e:
                    logger.error(f"Failed to commit transaction {transaction_id}: {str(e)}")
                    # We don't rollback here since individual operations may have succeeded
            
            return result
            
        except Exception as e:
            logger.error(f"Error in peer review workflow: {str(e)}")
            
            # Rollback the transaction if it was started
            if transaction_started:
                try:
                    self.memory_manager.sync_manager.rollback_transaction(transaction_id)
                    logger.debug(f"Rolled back transaction {transaction_id} due to error")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction {transaction_id}: {str(rollback_error)}")
            
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
