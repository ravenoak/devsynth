import builtins
import importlib
import sys

import pytest


@pytest.mark.medium
def test_import_memory_without_tinydb_succeeds(monkeypatch):
    """Importing memory module should succeed without tinydb installed.

    ReqID: N/A"""

    original_memory = sys.modules.pop("devsynth.application.memory", None)
    original_adapter = sys.modules.pop(
        "devsynth.application.memory.adapters.tinydb_memory_adapter", None
    )
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("tinydb"):
            raise ImportError("No module named 'tinydb'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    try:
        module = importlib.import_module("devsynth.application.memory")
        assert module.TinyDBMemoryAdapter is None
        assert "TinyDBMemoryAdapter" not in module.__all__
    finally:
        if original_memory is not None:
            sys.modules["devsynth.application.memory"] = original_memory
        else:
            sys.modules.pop("devsynth.application.memory", None)
        if original_adapter is not None:
            sys.modules[
                "devsynth.application.memory.adapters.tinydb_memory_adapter"
            ] = original_adapter
        else:
            sys.modules.pop(
                "devsynth.application.memory.adapters.tinydb_memory_adapter", None
            )
