from __future__ import annotations

"""Peer review utilities for WSDE teams."""

from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass, field

from .message_protocol import MessageType


@dataclass
class PeerReview:
    """Represents a peer review cycle for a work product."""

    work_product: Any
    author: Any
    reviewers: List[Any]
    send_message: Optional[Callable[..., Any]] = None

    reviews: Dict[Any, Dict[str, Any]] = field(default_factory=dict)
    revision: Any = None
    status: str = "pending"

    def assign_reviews(self) -> None:
        """Notify reviewers of the review request."""

        if self.send_message:
            for reviewer in self.reviewers:
                self.send_message(
                    sender=getattr(self.author, "name", str(self.author)),
                    recipients=[getattr(reviewer, "name", str(reviewer))],
                    message_type=MessageType.REVIEW_REQUEST,
                    subject="Peer Review Request",
                    content={"work_product": self.work_product},
                )

    def collect_reviews(self) -> Dict[Any, Dict[str, Any]]:
        """Gather feedback from all reviewers."""

        for reviewer in self.reviewers:
            if hasattr(reviewer, "process"):
                result = reviewer.process({"work_product": self.work_product})
            else:
                result = {"feedback": "ok"}
            self.reviews[reviewer] = result
        return self.reviews

    def aggregate_feedback(self) -> Dict[str, Any]:
        """Aggregate feedback from reviewers into a single structure."""

        feedback = [r.get("feedback", "") for r in self.reviews.values()]
        return {"feedback": feedback}

    def request_revision(self) -> None:
        """Mark the review as requiring revision."""

        self.status = "revision_requested"

    def submit_revision(self, revision: Any) -> None:
        """Submit a revised work product for further review."""

        self.revision = revision
        self.status = "revised"

    def finalize(self, approved: bool = True) -> Dict[str, Any]:
        """Finalize the peer review and return aggregated feedback."""

        self.status = "approved" if approved else "rejected"
        feedback = self.aggregate_feedback()
        return {"status": self.status, "feedback": feedback}


@dataclass
class PeerReviewWorkflow:
    """Encapsulates a full peer review workflow."""

    work_product: Any
    author: Any
    reviewers: List[Any]
    send_message: Optional[Callable[..., Any]] = None

    def run(self) -> Dict[str, Any]:
        review = PeerReview(
            work_product=self.work_product,
            author=self.author,
            reviewers=self.reviewers,
            send_message=self.send_message,
        )
        review.assign_reviews()
        review.collect_reviews()
        return review.finalize()


def run_peer_review(
    work_product: Any,
    author: Any,
    reviewers: List[Any],
    send_message: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    """Convenience function to execute a full peer review."""

    workflow = PeerReviewWorkflow(
        work_product=work_product,
        author=author,
        reviewers=reviewers,
        send_message=send_message,
    )
    return workflow.run()
