from __future__ import annotations

import importlib.util
import sys
from collections.abc import Mapping
from types import ModuleType
from unittest.mock import MagicMock

import pytest


def _create_stub(name: str, attrs: Mapping[str, object] | None = None) -> ModuleType:
    """Create a simple module stub with optional attributes."""
    mod = ModuleType(name)
    # Flag DevSynth-created stubs so resource gating can treat them as unavailable.
    setattr(mod, "__devsynth_optional_stub__", True)
    if attrs:
        for key, value in attrs.items():
            setattr(mod, key, value)
    return mod


def _apply_optional_stubs():
    """Apply optional dependency stubs globally for test environment.

    This function applies the same stubs as the stub_optional_deps fixture
    but can be called directly during conftest initialization.
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
        "duckdb": {
            "connect": lambda *a, **k: MagicMock(),
        },
        "lmdb": {
            "open": lambda *a, **k: MagicMock(),
            "Environment": MagicMock,
        },
        "faiss": {
            "IndexFlatIP": MagicMock,
            "IndexIVFFlat": MagicMock,
        },
        "httpx": {
            "Client": MagicMock,
            "AsyncClient": MagicMock,
        },
        "kuzu": {
            "Database": MagicMock,
            "Connection": MagicMock,
        },
        "chromadb": {
            "Client": MagicMock,
            "PersistentClient": MagicMock,
            "HttpClient": MagicMock,
        },
        "tinydb": {
            "TinyDB": MagicMock,
            "Query": MagicMock,
        },
        "numpy": {
            "array": lambda x: x,
            "dot": lambda a, b: 0.0,
            "zeros": lambda *a, **k: [],
            "ones": lambda *a, **k: [1],
            "isscalar": lambda obj: not isinstance(obj, (list, tuple, set, dict)),
        },
        "rdflib": {
            "Graph": MagicMock,
            "Namespace": MagicMock,
            "URIRef": MagicMock,
            "Literal": MagicMock,
        },
        "prometheus_client": {
            "Counter": object,
            "Histogram": object,
            "generate_latest": lambda *a, **k: b"",
            "CONTENT_TYPE_LATEST": "text/plain; version=0.0.4; charset=utf-8",
        },
    }

    for name, attrs in modules.items():
        if name == "numpy" and importlib.util.find_spec("numpy") is not None:
            continue
        if name not in sys.modules:
            sys.modules[name] = _create_stub(name, attrs)


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
        "duckdb": {
            "connect": lambda *a, **k: MagicMock(),
        },
        "lmdb": {
            "open": lambda *a, **k: MagicMock(),
            "Environment": MagicMock,
        },
        "faiss": {
            "IndexFlatIP": MagicMock,
            "IndexIVFFlat": MagicMock,
        },
        "httpx": {
            "Client": MagicMock,
            "AsyncClient": MagicMock,
        },
        "kuzu": {
            "Database": MagicMock,
            "Connection": MagicMock,
        },
        "chromadb": {
            "Client": MagicMock,
            "PersistentClient": MagicMock,
            "HttpClient": MagicMock,
        },
        "tinydb": {
            "TinyDB": MagicMock,
            "Query": MagicMock,
        },
        "numpy": {
            "array": lambda x: x,
            "dot": lambda a, b: 0.0,
            "zeros": lambda *a, **k: [],
            "ones": lambda *a, **k: [1],
            "isscalar": lambda obj: not isinstance(obj, (list, tuple, set, dict)),
        },
        "rdflib": {
            "Graph": MagicMock,
            "Namespace": MagicMock,
            "URIRef": MagicMock,
            "Literal": MagicMock,
        },
        "prometheus_client": {
            "Counter": object,
            "Histogram": object,
            "generate_latest": lambda *a, **k: b"",
            "CONTENT_TYPE_LATEST": "text/plain; version=0.0.4; charset=utf-8",
        },
    }

    for name, attrs in modules.items():
        if name == "numpy" and importlib.util.find_spec("numpy") is not None:
            continue
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
