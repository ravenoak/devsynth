import builtins
import importlib
import sys


def test_import_lmstudio_provider_without_lmstudio_succeeds(monkeypatch):
    """Importing providers should succeed without lmstudio installed."""
    sys.modules.pop("devsynth.application.llm.providers", None)
    sys.modules.pop("devsynth.application.llm.lmstudio_provider", None)
    sys.modules.pop("lmstudio", None)
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("lmstudio"):
            raise ImportError("No module named 'lmstudio'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    providers = importlib.import_module("devsynth.application.llm.providers")
    assert providers.LMStudioProvider is None
    assert "lmstudio" not in providers.factory.provider_types
