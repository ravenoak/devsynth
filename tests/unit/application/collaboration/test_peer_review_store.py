from unittest.mock import patch

import pytest

from devsynth.application.collaboration.peer_review import PeerReview


class DummyMemoryManager:
    def __init__(self) -> None:
        self.adapters = {"tinydb": object()}
        self.flushed = False

    def flush_updates(self) -> None:
        self.flushed = True


@pytest.mark.fast
def test_store_in_memory_uses_retry_and_flush() -> None:
    """ReqID: N/A"""

    mm = DummyMemoryManager()
    review = PeerReview(
        work_product="wp", author="a", reviewers=["r"], memory_manager=mm
    )

    with patch(
        "devsynth.application.collaboration."
        "collaboration_memory_utils.store_with_retry",
        return_value="id123",
    ) as mock_store:
        item_id = review.store_in_memory()

    mock_store.assert_called_once_with(
        mm,
        review,
        primary_store="tinydb",
        immediate_sync=False,
        max_retries=3,
    )
    assert item_id == "id123"
    assert mm.flushed is True
