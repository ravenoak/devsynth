import builtins
import importlib
import sys

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "optional_tinydb_dependency.feature"))


@pytest.fixture
def context():
    class Context:
        module = None

    return Context()


@pytest.fixture
def simulate_missing_tinydb(monkeypatch):
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
    yield
    if original_memory is not None:
        sys.modules["devsynth.application.memory"] = original_memory
    else:
        sys.modules.pop("devsynth.application.memory", None)
    if original_adapter is not None:
        sys.modules["devsynth.application.memory.adapters.tinydb_memory_adapter"] = (
            original_adapter
        )
    else:
        sys.modules.pop(
            "devsynth.application.memory.adapters.tinydb_memory_adapter", None
        )


@given("TinyDB is not installed")
def given_tinydb_not_installed(simulate_missing_tinydb):
    pass


@when("the memory module is imported")
def when_import_memory(context):
    context.module = importlib.import_module("devsynth.application.memory")


@then("the TinyDB adapter is unavailable")
def then_no_tinydb_adapter(context):
    assert context.module.TinyDBMemoryAdapter is None
    assert "TinyDBMemoryAdapter" not in context.module.__all__
