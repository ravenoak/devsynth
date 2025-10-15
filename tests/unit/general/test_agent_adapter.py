import pytest

from devsynth.adapters.agents.agent_adapter import SimplifiedAgentFactory


@pytest.mark.medium
def test_register_agent_type_succeeds():
    """Test that register agent type succeeds.

    ReqID: N/A"""
    factory = SimplifiedAgentFactory()

    class Dummy: ...

    factory.register_agent_type("dummy", Dummy)
    assert "dummy" in factory._custom_agents
    assert factory._custom_agents["dummy"] is Dummy
