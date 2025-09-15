import json
from types import SimpleNamespace

import pytest

from devsynth.application.agents.wsde_memory_integration import WSDEMemoryIntegration


class DummyAgentMemory:
    def __init__(self) -> None:
        self.store_calls = []

    def store_dialectical_reasoning(self, task_id, thesis, antithesis, synthesis):
        self.store_calls.append((task_id, thesis, antithesis, synthesis))
        return "m1"

    def retrieve_dialectical_reasoning(self, task_id):
        return SimpleNamespace(
            content=json.dumps({"thesis": 1, "antithesis": 2, "synthesis": 3})
        )


@pytest.mark.fast
def test_store_and_retrieve_dialectical_process() -> None:
    """ReqID: N/A"""

    adapter = SimpleNamespace(get_context_manager=lambda: None)
    team = SimpleNamespace()
    memory = DummyAgentMemory()
    integration = WSDEMemoryIntegration(adapter, team, agent_memory=memory)
    task = {"id": "t1"}

    item_id = integration.store_dialectical_process(task, {}, {}, {})
    assert item_id == "m1"
    assert memory.store_calls[0][0] == "t1"

    result = integration.retrieve_dialectical_process("t1")
    assert result == {"thesis": 1, "antithesis": 2, "synthesis": 3}
