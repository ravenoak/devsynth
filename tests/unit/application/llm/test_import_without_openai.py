import builtins
import importlib
import sys

import pytest


@pytest.mark.fast
def test_import_openai_provider_without_openai_succeeds(monkeypatch):
    """Importing OpenAI provider should succeed without openai installed."""
    sys.modules.pop("devsynth.application.llm.openai_provider", None)
    sys.modules.pop("openai", None)
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("openai"):
            raise ImportError("No module named 'openai'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    module = importlib.import_module("devsynth.application.llm.openai_provider")
    assert module.OpenAI is object


@pytest.mark.fast
def test_openai_provider_requires_api_key(monkeypatch):
    """Missing API key should raise a clear error."""
    sys.modules.pop("devsynth.application.llm.openai_provider", None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    module = importlib.import_module("devsynth.application.llm.openai_provider")
    with pytest.raises(module.OpenAIConnectionError) as exc:
        module.OpenAIProvider({})
    assert "OpenAI API key is required" in str(exc.value)
