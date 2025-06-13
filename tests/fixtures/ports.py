"""Example fixtures for mocking DevSynth ports."""

import pytest

from devsynth.ports.llm_port import LLMPort
from devsynth.adapters.llm.mock_llm_adapter import MockLLMAdapter
from devsynth.ports.memory_port import MemoryPort
from devsynth.domain.interfaces.memory import MemoryStore, ContextManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.ports.onnx_port import OnnxPort
from tests.unit.fakes.fake_onnx_runtime import FakeOnnxRuntime


class _InMemoryStore(MemoryStore):
    def __init__(self):
        self.items = {}

    def store(self, item: MemoryItem) -> str:
        item_id = item.id or str(len(self.items))
        item.id = item_id
        self.items[item_id] = item
        return item_id

    def retrieve(self, item_id: str):
        return self.items.get(item_id)

    def search(self, query: dict):
        return list(self.items.values())

    def delete(self, item_id: str) -> bool:
        return self.items.pop(item_id, None) is not None


class _SimpleContextManager(ContextManager):
    def __init__(self):
        self.ctx = {}

    def add_to_context(self, key: str, value):
        self.ctx[key] = value

    def get_from_context(self, key: str):
        return self.ctx.get(key)

    def get_full_context(self):
        return dict(self.ctx)

    def clear_context(self):
        self.ctx.clear()


class _MockProviderFactory:
    def create_provider(self, provider_type: str, config=None):
        return MockLLMAdapter()

    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        pass


@pytest.fixture
def llm_port():
    """Provide an LLMPort using the MockLLMAdapter."""
    port = LLMPort(_MockProviderFactory())
    port.set_default_provider("mock")
    return port


@pytest.fixture
def memory_port():
    """Provide a MemoryPort using in-memory stores."""
    return MemoryPort(_SimpleContextManager(), _InMemoryStore())


@pytest.fixture
def onnx_port():
    """Provide an OnnxPort with a fake runtime."""
    return OnnxPort(FakeOnnxRuntime())
