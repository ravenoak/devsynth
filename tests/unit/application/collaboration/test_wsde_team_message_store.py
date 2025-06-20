from unittest.mock import MagicMock
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.collaboration.message_protocol import (
    MessageStore,
    MessageProtocol,
    MessageType,
)


def test_team_message_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
    store = MessageStore(str(tmp_path / "msgs.json"))
    protocol = MessageProtocol(store)
    team = WSDETeam(message_protocol=protocol)

    sender = MagicMock()
    sender.name = "a"
    recipient = MagicMock()
    recipient.name = "b"
    team.add_agents([sender, recipient])

    team.send_message("a", ["b"], MessageType.NOTIFICATION, "subj", "content")

    # reload protocol via store
    new_team = WSDETeam(message_protocol=MessageProtocol(store))
    msgs = new_team.get_messages()
    assert len(msgs) == 1
    assert msgs[0].subject == "subj"
