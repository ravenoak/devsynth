from __future__ import annotations

import sys
from types import ModuleType
from typing import Mapping

import pytest


def _create_stub(name: str, attrs: Mapping[str, object] | None = None) -> ModuleType:
    """Create a simple module stub with optional attributes."""
    mod = ModuleType(name)
    if attrs:
        for key, value in attrs.items():
            setattr(mod, key, value)
    return mod


@pytest.fixture
def stub_optional_deps(monkeypatch):
    """Provide lightweight stubs for optional heavy dependencies.

    Stubs are only applied when the modules are missing, preventing expensive
    imports during test collection while allowing tests to run against a
    predictable interface.
    """

    modules = {
        "langgraph": {},
        "langgraph.checkpoint": {},
        "langgraph.checkpoint.base": {
            "BaseCheckpointSaver": object,
            "empty_checkpoint": object(),
        },
        "langgraph.graph": {"END": None, "StateGraph": object},
        "tiktoken": {"encoding_for_model": lambda *a, **k: None},
        "duckdb": {},
        "lmdb": {},
        "faiss": {},
        "httpx": {},
    }

    for name, attrs in modules.items():
        if name not in sys.modules:
            monkeypatch.setitem(sys.modules, name, _create_stub(name, attrs))


@pytest.fixture
def require_modules():
    """Skip the test if any of the specified modules are missing."""

    def _require(*module_names: str) -> None:
        missing = [m for m in module_names if m not in sys.modules]
        if missing:
            pytest.skip("Missing required modules: " + ", ".join(missing))

    return _require
