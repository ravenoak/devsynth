"""Example fixtures for mocking DevSynth ports."""

import pytest

try:  # pragma: no cover - optional dependency for adapter unit tests
    from devsynth.adapters.llm.mock_llm_adapter import MockLLMAdapter
except Exception as import_error:  # pragma: no cover - defensive guard
    MockLLMAdapter = None  # type: ignore[assignment]
    _MOCK_IMPORT_ERROR = import_error
else:
    _MOCK_IMPORT_ERROR = None
from devsynth.domain.interfaces.memory import ContextManager, MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.ports.llm_port import LLMPort
from devsynth.ports.memory_port import MemoryPort
from devsynth.ports.onnx_port import OnnxPort
from tests.unit.fakes.test_fake_onnx_runtime import FakeOnnxRuntime


class _InMemoryStore(MemoryStore):
    def __init__(self):
        self.items = {}
        self._tx_snapshots: dict[str, dict[str, MemoryItem]] = {}

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

    # Transaction methods expected by MemoryStore protocol
    def begin_transaction(self) -> str:
        tx_id = str(len(self._tx_snapshots) + 1)
        self._tx_snapshots[tx_id] = dict(self.items)
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        return self._tx_snapshots.pop(transaction_id, None) is not None

    def rollback_transaction(self, transaction_id: str) -> bool:
        snapshot = self._tx_snapshots.pop(transaction_id, None)
        if snapshot is None:
            return False
        self.items = snapshot
        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        return transaction_id in self._tx_snapshots


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
            if MockLLMAdapter is None:
                pytest.skip(
                    "MockLLMAdapter unavailable",
                    allow_module_level=True,
                )
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
