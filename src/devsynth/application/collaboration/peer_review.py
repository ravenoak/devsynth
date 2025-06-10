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
