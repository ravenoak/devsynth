import pytest

import pytest

from devsynth.application.collaboration.agent_collaboration import (
    AgentCollaborationSystem,
    AgentMessage,
    MessageType,
)
from devsynth.application.collaboration.dto import AgentPayload


@pytest.mark.fast
def test_agent_message_to_dict() -> None:
    """ReqID: N/A"""

    payload = AgentPayload(attributes={"x": 1})
    msg = AgentMessage("a", "b", MessageType.TASK_ASSIGNMENT, payload)
    data = msg.to_dict()
    assert data["sender_id"] == "a"
    assert data["recipient_id"] == "b"
    assert data["message_type"] == "TASK_ASSIGNMENT"
    assert data["content"]["dto_type"] == "AgentPayload"
    assert data["content"]["attributes"] == {"x": 1}
    assert msg.content == {"x": 1}


class DummyMemoryManager:
    def __init__(self) -> None:
        self.adapters = {"tinydb": object()}
        self.updated = None
        self.flushed = False

    def update_item(self, store, item):
        self.updated = (store, item)

    def flush_updates(self):
        self.flushed = True


@pytest.mark.fast
def test_create_team_stores_in_memory() -> None:
    """ReqID: N/A"""

    mm = DummyMemoryManager()
    system = AgentCollaborationSystem(memory_manager=mm)

    class Agent:
        def __init__(self) -> None:
            self.id = "a1"
            self.name = "agent1"
            self.capabilities = ["code"]
            self.expertise = ["coding"]

    agent = Agent()
    system.register_agent(agent)
    team = system.create_team("t1", ["a1"])

    assert mm.updated[0] == "tinydb"
    assert mm.flushed is True
    assert team.agents[0] is agent
