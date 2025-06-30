import sys
import types

# Stub modules that require optional dependencies
mem_mod = types.ModuleType('devsynth.adapters.memory.memory_adapter')
class MemorySystemAdapter:
    def get_memory_store(self):
        return {}
mem_mod.MemorySystemAdapter = MemorySystemAdapter
sys.modules['devsynth.adapters.memory.memory_adapter'] = mem_mod

am_mod = types.ModuleType('devsynth.application.agents.agent_memory_integration')
am_mod.AgentMemoryIntegration = object
sys.modules['devsynth.application.agents.agent_memory_integration'] = am_mod

wsde_mod = types.ModuleType('devsynth.application.agents.wsde_memory_integration')
wsde_mod.WSDEMemoryIntegration = object
sys.modules['devsynth.application.agents.wsde_memory_integration'] = wsde_mod

from devsynth.application.agents.unified_agent import UnifiedAgent


def test_process_generic_task():
    agent = UnifiedAgent()
    result = agent._process_generic_task({"foo": "bar"})
    assert "result" in result
    assert result["wsde"].metadata["type"] == "generic"
