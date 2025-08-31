pytest_plugins = ["tests.fixtures.ports"]
import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.mark.fast
def test_ports_fixtures_succeeds(llm_port, memory_port, onnx_port):
    """Test that ports fixtures succeeds.

    ReqID: N/A"""
    response = llm_port.generate("Tell me a joke")
    assert "mock" in response.lower()
    item = MemoryItem(id="", content="data", memory_type=MemoryType.WORKING)
    item_id = memory_port.store_memory(item.content, item.memory_type)
    retrieved = memory_port.retrieve_memory(item_id)
    assert retrieved.content == "data"
    onnx_port.load_model("model.onnx")
    result = list(onnx_port.run({"x": [1]}))
    assert result == [{"x": [1]}]
