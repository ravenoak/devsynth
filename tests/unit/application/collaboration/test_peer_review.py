import pytest
from unittest.mock import MagicMock
from devsynth.application.collaboration.peer_review import PeerReview
from devsynth.application.collaboration.message_protocol import MessageType


def test_aggregate_feedback_with_reviewers():
    author = MagicMock(name="author")
    reviewer1 = MagicMock()
    reviewer1.name = "r1"
    reviewer2 = MagicMock()
    reviewer2.name = "r2"
    reviewer1.process = MagicMock(return_value={"feedback": "f1"})
    reviewer2.process = MagicMock(return_value={"feedback": "f2"})

    review = PeerReview(
        work_product="work", author=author, reviewers=[reviewer1, reviewer2]
    )
    review.collect_reviews()
    aggregated = review.aggregate_feedback()

    feedback = aggregated["feedback"]
    assert {"reviewer": "r1", "feedback": "f1"} in feedback
    assert {"reviewer": "r2", "feedback": "f2"} in feedback
