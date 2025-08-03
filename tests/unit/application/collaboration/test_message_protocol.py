import pytest
from devsynth.application.collaboration.message_protocol import MessageProtocol, MessageType

@pytest.mark.medium
def test_send_message_priority_succeeds():
    """Test that send message priority succeeds.

ReqID: N/A"""
    proto = MessageProtocol()
    proto.send_message(sender='a', recipients=['b'], message_type=MessageType.STATUS_UPDATE, subject='s', content='c', metadata={'priority': 'high'})
    proto.send_message(sender='a', recipients=['b'], message_type=MessageType.STATUS_UPDATE, subject='s2', content='c2', metadata={})
    assert proto.history[0].metadata.get('priority') == 'high'

@pytest.mark.medium
def test_get_messages_filtered_succeeds():
    """Test that get messages filtered succeeds.

ReqID: N/A"""
    proto = MessageProtocol()
    msg = proto.send_message(sender='a', recipients=['b'], message_type=MessageType.DECISION_REQUEST, subject='x', content='y', metadata={})
    result = proto.get_messages('b', {'message_type': MessageType.DECISION_REQUEST})
    assert result == [msg]