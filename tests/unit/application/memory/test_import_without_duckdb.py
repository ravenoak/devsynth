import builtins
import importlib
import sys

import pytest


@pytest.mark.medium
def test_init_duckdb_store_without_duckdb_fails(monkeypatch, tmp_path):
    """DuckDBStore initialization should fail when duckdb is missing."""
    sys.modules.pop("devsynth.application.memory.duckdb_store", None)
    sys.modules.pop("duckdb", None)
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "duckdb":
            raise ImportError("No module named 'duckdb'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    module = importlib.import_module("devsynth.application.memory.duckdb_store")
    module.DuckDBStore.__abstractmethods__ = frozenset()
    with pytest.raises(ImportError, match="duckdb"):
        module.DuckDBStore(str(tmp_path))
