import sys
import types

import pytest


@pytest.fixture(autouse=True)
def stub_agent_dependencies(monkeypatch):
    """Stub heavy agent dependencies to avoid imports during testing."""
    mem_mod = types.ModuleType("devsynth.adapters.memory.memory_adapter")

    class MemorySystemAdapter:

        def get_memory_store(self):
            return {}

    mem_mod.MemorySystemAdapter = MemorySystemAdapter
    monkeypatch.setitem(sys.modules, "devsynth.adapters.memory.memory_adapter", mem_mod)
    am_mod = types.ModuleType("devsynth.application.agents.agent_memory_integration")
    am_mod.AgentMemoryIntegration = object
    monkeypatch.setitem(
        sys.modules, "devsynth.application.agents.agent_memory_integration", am_mod
    )
    wsde_mod = types.ModuleType("devsynth.application.agents.wsde_memory_integration")
    wsde_mod.WSDEMemoryIntegration = object
    monkeypatch.setitem(
        sys.modules, "devsynth.application.agents.wsde_memory_integration", wsde_mod
    )
    yield


def import_unified_agent():
    """Import the ``UnifiedAgent`` after stubbing its dependencies."""
    from devsynth.application.agents.unified_agent import UnifiedAgent

    return UnifiedAgent


@pytest.mark.medium
def test_process_generic_task_succeeds():
    """Test that process generic task succeeds.

    ReqID: N/A"""
    UnifiedAgent = import_unified_agent()
    agent = UnifiedAgent()
    result = agent._process_generic_task({"foo": "bar"})
    assert "result" in result
    assert result["wsde"].metadata["type"] == "generic"
