import pytest

from devsynth.application.memory.adapters import tinydb_memory_adapter as mod

pytestmark = pytest.mark.fast


def test_tinydb_adapter_raises_import_error_on_stub(monkeypatch):
    """Ensure adapter fails gracefully when TinyDB is a stub.

    ReqID: DSY-0001
    """
    monkeypatch.setattr(mod, "TinyDB", object)
    with pytest.raises(ImportError):
        mod.TinyDBMemoryAdapter()
