import logging
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from devsynth.domain.models.wsde_utils import (
    add_solution,
    broadcast_message,
    conduct_peer_review,
    get_messages,
    request_peer_review,
    send_message,
)

pytestmark = [pytest.mark.fast]


class DummyAgent(SimpleNamespace):
    pass


def test_send_message_invokes_protocol():
    team = SimpleNamespace(message_protocol=MagicMock())
    team.message_protocol.send_message.return_value = "msg-id"
    result = send_message(
        team,
        sender="alice",
        recipients=["bob"],
        message_type="info",
        subject="hi",
        content={"x": 1},
        metadata={"y": 2},
    )
    team.message_protocol.send_message.assert_called_once_with(
        sender="alice",
        recipients=["bob"],
        message_type="info",
        subject="hi",
        content={"x": 1},
        metadata={"y": 2},
    )
    assert result == "msg-id"


def test_broadcast_message_excludes_sender():
    team = SimpleNamespace(message_protocol=MagicMock())
    team.message_protocol.send_message.return_value = "broadcast-id"
    team.agents = [
        DummyAgent(name="alice"),
        DummyAgent(name="bob"),
        DummyAgent(name="carol"),
    ]
    result = broadcast_message(team, sender="alice", message_type="notice")
    team.message_protocol.send_message.assert_called_once()
    kwargs = team.message_protocol.send_message.call_args.kwargs
    assert kwargs["recipients"] == ["bob", "carol"]
    assert result == "broadcast-id"


def test_get_messages_uses_protocol():
    team = SimpleNamespace(message_protocol=MagicMock())
    team.message_protocol.get_messages.return_value = ["m1", "m2"]
    msgs = get_messages(team, agent="alice", filters={"type": "info"})
    team.message_protocol.get_messages.assert_called_once_with(
        "alice", {"type": "info"}
    )
    assert msgs == ["m1", "m2"]


@patch("devsynth.application.collaboration.peer_review.PeerReview")
def test_request_peer_review_creates_cycle(mock_peer_review):
    team = SimpleNamespace(peer_reviews=[])
    review = MagicMock()
    mock_peer_review.return_value = review
    result = request_peer_review(team, "work", "author", ["r1", "r2"])
    mock_peer_review.assert_called_once()
    review.assign_reviews.assert_called_once()
    assert team.peer_reviews == [review]
    assert result is review


@patch("devsynth.domain.models.wsde_utils.request_peer_review")
def test_conduct_peer_review_collects_feedback(mock_request):
    review = MagicMock()
    review.aggregate_feedback.return_value = {"score": 5}
    mock_request.return_value = review
    result = conduct_peer_review(SimpleNamespace(), "work", "author", ["r1"])
    review.collect_reviews.assert_called_once()
    review.aggregate_feedback.assert_called_once()
    assert review.status == "completed"
    assert result == {"review": review, "feedback": {"score": 5}}


@patch("devsynth.domain.models.wsde_utils.request_peer_review", return_value=None)
def test_conduct_peer_review_handles_missing_peer_review(mock_request):
    result = conduct_peer_review(SimpleNamespace(), "work", "author", ["r1"])
    assert result == {"review": None, "feedback": {}}


def test_add_solution_appends_and_triggers_hooks():
    hook = MagicMock()
    team = SimpleNamespace(solutions={}, dialectical_hooks=[hook])
    task = {"id": "t1"}
    solution = {"content": "data"}
    result = add_solution(team, task, solution)
    assert team.solutions["t1"] == [solution]
    hook.assert_called_once_with(task, [solution])
    assert result == solution


def test_request_peer_review_logs_warning_on_failure(monkeypatch, caplog):
    module_name = "devsynth.application.collaboration.peer_review"
    fake_module = ModuleType("peer_review")
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    import devsynth.application.collaboration as collab_pkg

    monkeypatch.delattr(collab_pkg, "peer_review", raising=False)

    team = SimpleNamespace(peer_reviews=[])
    with caplog.at_level(logging.WARNING):
        result = request_peer_review(team, "work", "author", [])

    assert result is None
    assert any("Peer review failed" in r.message for r in caplog.records)
