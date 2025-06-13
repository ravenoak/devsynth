pytest_plugins = ["tests.fixtures.ports"]

from devsynth.domain.models.memory import MemoryItem, MemoryType


def test_ports_fixtures(llm_port, memory_port, onnx_port):
    # LLM port should generate mock responses
    response = llm_port.generate("Tell me a joke")
    assert "mock" in response.lower()

    # Memory port should store and retrieve items in memory
    item = MemoryItem(id="", content="data", memory_type=MemoryType.WORKING)
    item_id = memory_port.store_memory(item.content, item.memory_type)
    retrieved = memory_port.retrieve_memory(item_id)
    assert retrieved.content == "data"

    # ONNX port should echo inputs via the fake runtime
    onnx_port.load_model("model.onnx")
    result = list(onnx_port.run({"x": [1]}))
    assert result == [{"x": [1]}]
