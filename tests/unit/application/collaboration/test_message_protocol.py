import pytest
from devsynth.application.collaboration.message_protocol import (
    MessageProtocol,
    MessageType,
    MessageStore,
)


def test_send_message_priority():
    proto = MessageProtocol()
    proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.STATUS_UPDATE,
        subject="s",
        content="c",
        metadata={"priority": "high"},
    )
    proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.STATUS_UPDATE,
        subject="s2",
        content="c2",
        metadata={},
    )
    assert proto.history[0].metadata.get("priority") == "high"


def test_priority_ordering(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
    store = MessageStore(str(tmp_path / "msgs.json"))
    proto = MessageProtocol(store)
    low = proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.STATUS_UPDATE,
        subject="low",
        content="c",
        metadata={"priority": "low"},
    )
    normal = proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.STATUS_UPDATE,
        subject="norm",
        content="c",
        metadata={"priority": "normal"},
    )
    high = proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.STATUS_UPDATE,
        subject="high",
        content="c",
        metadata={"priority": "high"},
    )
    assert proto.history == [high, normal, low]

    # verify persistence
    proto2 = MessageProtocol(MessageStore(store.storage_file))
    assert [m.subject for m in proto2.history] == ["high", "norm", "low"]


def test_get_messages_filtered():
    proto = MessageProtocol()
    msg = proto.send_message(
        sender="a",
        recipients=["b"],
        message_type=MessageType.DECISION_REQUEST,
        subject="x",
        content="y",
        metadata={},
    )
    result = proto.get_messages("b", {"message_type": MessageType.DECISION_REQUEST})
    assert result == [msg]
