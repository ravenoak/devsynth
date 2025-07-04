from __future__ import annotations

"""Peer review utilities for WSDE teams."""

from typing import Any, Dict, List, Callable, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from .message_protocol import MessageType


@dataclass
class PeerReview:
    """Represents a peer review cycle for a work product."""

    work_product: Any
    author: Any
    reviewers: List[Any]
    send_message: Optional[Callable[..., Any]] = None
    acceptance_criteria: Optional[List[str]] = None
    quality_metrics: Optional[Dict[str, Any]] = None

    reviews: Dict[Any, Dict[str, Any]] = field(default_factory=dict)
    revision: Any = None
    revision_history: List[Any] = field(default_factory=list)
    status: str = "pending"
    review_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    previous_review: Optional['PeerReview'] = None
    quality_score: float = 0.0
    metrics_results: Dict[str, Any] = field(default_factory=dict)

    def assign_reviews(self) -> None:
        """Notify reviewers of the review request."""

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

    def collect_reviews(self) -> Dict[Any, Dict[str, Any]]:
        """Gather feedback from all reviewers."""

        self.updated_at = datetime.now()

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

                result = reviewer.process(process_input)
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

        # Calculate quality score if metrics are available
        self._calculate_quality_score()

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
                final_criteria[criterion] = sum(1 for r in results if r) > len(results) / 2

            result["criteria_results"] = final_criteria
            result["all_criteria_passed"] = all(final_criteria.values())

        # Add metrics results if available
        if self.metrics_results:
            result["metrics_results"] = self.metrics_results

        # Add dialectical analysis if available
        dialectical_analysis = {}
        for review in self.reviews.values():
            for key in ["thesis", "antithesis", "synthesis"]:
                if key in review:
                    dialectical_analysis[key] = review[key]

        if dialectical_analysis:
            result["dialectical_analysis"] = dialectical_analysis

        return result

    def request_revision(self) -> None:
        """Mark the review as requiring revision."""

        self.updated_at = datetime.now()
        self.status = "revision_requested"

    def submit_revision(self, revision: Any) -> 'PeerReview':
        """
        Submit a revised work product for further review.

        Returns:
            A new PeerReview instance linked to this one.
        """
        self.updated_at = datetime.now()
        self.revision = revision
        self.revision_history.append(revision)
        self.status = "revised"

        # Create a new review for the revision, linked to this one
        new_review = PeerReview(
            work_product=revision,
            author=self.author,
            reviewers=self.reviewers,
            send_message=self.send_message,
            acceptance_criteria=self.acceptance_criteria,
            quality_metrics=self.quality_metrics,
            previous_review=self
        )

        return new_review

    def finalize(self, approved: bool = True) -> Dict[str, Any]:
        """Finalize the peer review and return aggregated feedback."""

        self.updated_at = datetime.now()
        self.status = "approved" if approved else "rejected"

        # Determine if all criteria passed (if applicable)
        all_criteria_passed = True
        if self.acceptance_criteria:
            feedback = self.aggregate_feedback()
            all_criteria_passed = feedback.get("all_criteria_passed", False)

            # Override approval if criteria failed
            if not all_criteria_passed and approved:
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

        # Include revision history
        if self.revision_history:
            result["revisions"] = {
                "count": len(self.revision_history),
                "history": self.revision_history
            }

        # Include previous review reference
        if self.previous_review:
            result["previous_review_id"] = self.previous_review.review_id

        return result


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

    def run(self) -> Dict[str, Any]:
        """
        Run a complete peer review workflow with support for revision cycles.

        Returns:
            Dict containing the final review results.
        """
        review = PeerReview(
            work_product=self.work_product,
            author=self.author,
            reviewers=self.reviewers,
            send_message=self.send_message,
            acceptance_criteria=self.acceptance_criteria,
            quality_metrics=self.quality_metrics,
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
        while (not all_criteria_passed or quality_score < 0.7) and revision_count < self.max_revision_cycles:
            current_review.request_revision()

            # In a real implementation, this would involve getting the revised work product
            # from the author. For now, we'll simulate a revision by creating a copy.
            revised_work = {
                "original": current_review.work_product,
                "revision": f"Revision {revision_count + 1}",
                "improvements": "Addressed reviewer feedback"
            }

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
            "all_criteria_passed": all_criteria_passed
        }

        return result


def run_peer_review(
    work_product: Any,
    author: Any,
    reviewers: List[Any],
    send_message: Optional[Callable[..., Any]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    quality_metrics: Optional[Dict[str, Any]] = None,
    max_revision_cycles: int = 3,
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

    Returns:
        Dict containing the final review results
    """
    workflow = PeerReviewWorkflow(
        work_product=work_product,
        author=author,
        reviewers=reviewers,
        send_message=send_message,
        acceptance_criteria=acceptance_criteria,
        quality_metrics=quality_metrics,
        max_revision_cycles=max_revision_cycles,
    )
    return workflow.run()
