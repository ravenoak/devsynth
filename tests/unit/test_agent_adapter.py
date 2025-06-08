from devsynth.adapters.agents.agent_adapter import SimplifiedAgentFactory


def test_register_agent_type():
    factory = SimplifiedAgentFactory()

    class Dummy:
        ...

    factory.register_agent_type("dummy", Dummy)
    assert "dummy" in factory.agent_types
