import builtins
import importlib
import sys


def test_import_memory_without_tinydb_succeeds(monkeypatch):
    """Importing memory module should succeed without tinydb installed.

ReqID: N/A"""
    sys.modules.pop('devsynth.application.memory', None)
    sys.modules.pop(
        'devsynth.application.memory.adapters.tinydb_memory_adapter', None)
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith('tinydb'):
            raise ImportError("No module named 'tinydb'")
        return real_import(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, '__import__', fake_import)
    module = importlib.import_module('devsynth.application.memory')
    assert module.TinyDBMemoryAdapter is None
    assert 'TinyDBMemoryAdapter' not in module.__all__
