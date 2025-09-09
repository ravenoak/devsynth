import builtins
import importlib
import importlib.util
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location(
    "devsynth.application.llm.offline_provider",
    ROOT / "src/devsynth/application/llm/offline_provider.py",
)
offline_provider = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = offline_provider
spec.loader.exec_module(offline_provider)


def _reload_provider():
    importlib.reload(offline_provider)


@pytest.mark.medium
def test_load_transformer_deps_imports_when_available(monkeypatch):
    _reload_provider()
    dummy_torch = types.SimpleNamespace(
        no_grad=lambda: contextmanager(lambda: (yield None))()
    )
    dummy_trans = types.SimpleNamespace(
        AutoModelForCausalLM="Model", AutoTokenizer="Tok"
    )
    monkeypatch.setitem(sys.modules, "torch", dummy_torch)
    monkeypatch.setitem(sys.modules, "transformers", dummy_trans)
    offline_provider.torch = None
    offline_provider.AutoModelForCausalLM = None
    offline_provider.AutoTokenizer = None
    offline_provider._load_transformer_deps()
    assert offline_provider.torch is dummy_torch
    assert offline_provider.AutoModelForCausalLM == "Model"
    assert offline_provider.AutoTokenizer == "Tok"


@pytest.mark.medium
def test_load_transformer_deps_noop_when_already_loaded(monkeypatch):
    _reload_provider()
    sentinel = object()
    offline_provider.torch = sentinel
    offline_provider.AutoModelForCausalLM = sentinel
    offline_provider.AutoTokenizer = sentinel
    offline_provider._load_transformer_deps()
    assert offline_provider.torch is sentinel
    assert offline_provider.AutoModelForCausalLM is sentinel
    assert offline_provider.AutoTokenizer is sentinel


@pytest.mark.medium
def test_load_transformer_deps_handles_import_error(monkeypatch):
    _reload_provider()
    offline_provider.torch = None
    offline_provider.AutoModelForCausalLM = None
    offline_provider.AutoTokenizer = None
    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {"torch", "transformers"}:
            raise ImportError("missing")
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    offline_provider._load_transformer_deps()
    assert offline_provider.torch is None
    assert offline_provider.AutoModelForCausalLM is None
    assert offline_provider.AutoTokenizer is None
    monkeypatch.setattr(builtins, "__import__", orig_import)
