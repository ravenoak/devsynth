import builtins
import importlib
import sys

import pytest


@pytest.mark.medium
def test_import_memory_with_tinydb_available_succeeds():
    """Importing memory module should succeed when tinydb is available.

    ReqID: N/A"""
    try:
        import tinydb
        tinydb_available = True
    except ImportError:
        tinydb_available = False

    module = importlib.import_module("devsynth.application.memory")

    if tinydb_available:
        # When tinydb is available, TinyDBMemoryAdapter should be available
        assert module.TinyDBMemoryAdapter is not None
        assert "TinyDBMemoryAdapter" in module.__all__
    else:
        # When tinydb is not available, TinyDBMemoryAdapter should be None
        assert module.TinyDBMemoryAdapter is None
        assert "TinyDBMemoryAdapter" not in module.__all__
