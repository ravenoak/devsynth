import builtins
import importlib
import sys

import pytest


@pytest.mark.medium
def test_import_lmstudio_provider_without_lmstudio_succeeds(monkeypatch):
    """Importing providers should succeed without lmstudio installed.

    ReqID: LMSTUDIO-2"""
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


@pytest.mark.medium
def test_factory_missing_lmstudio_provider_raises_clear_error(monkeypatch):
    """Requesting LM Studio provider without SDK yields a helpful error.

    ReqID: LMSTUDIO-3"""
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
    with pytest.raises(
        providers.ValidationError, match="LMStudio provider is unavailable"
    ):
        providers.factory.create_provider("lmstudio")
