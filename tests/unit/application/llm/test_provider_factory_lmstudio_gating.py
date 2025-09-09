import importlib
import os
import types

import pytest

from devsynth.application.llm.provider_factory import ProviderFactory


@pytest.mark.fast
def test_lmstudio_not_selected_when_flag_false(monkeypatch):
    # Ensure env flags are false/unset
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    # Create a fresh factory instance to avoid module import side effects
    factory = ProviderFactory()

    class DummyLocal:
        def __init__(self, config=None):
            self.config = config

    class DummyLMStudio:
        def __init__(self, config=None):
            self.config = config

    factory.register_provider_type("local", DummyLocal)
    factory.register_provider_type("lmstudio", DummyLMStudio)

    # Implicit selection should skip lmstudio when flag is false, picking local
    provider = factory.create_provider()
    assert isinstance(provider, DummyLocal)


@pytest.mark.fast
def test_lmstudio_selected_when_flag_true(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    factory = ProviderFactory()

    class DummyLocal:
        def __init__(self, config=None):
            self.config = config

    class DummyLMStudio:
        def __init__(self, config=None):
            self.config = config

    # Register only these two to simplify ordering
    factory.register_provider_type("local", DummyLocal)
    factory.register_provider_type("lmstudio", DummyLMStudio)

    # With flag true and offline false, order prefers offline->local->openai->anthropic->lmstudio
    # Since offline is disabled and local is present, factory will select local first unless we request lmstudio explicitly.
    # Verify explicit request is honored when flag true.
    provider = factory.create_provider("lmstudio")
    assert isinstance(provider, DummyLMStudio)


@pytest.mark.fast
def test_offline_killswitch_overrides_explicit_selection(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")

    factory = ProviderFactory()

    class DummyOffline:
        def __init__(self, config=None):
            self.config = config

    class DummyLMStudio:
        def __init__(self, config=None):
            self.config = config

    factory.register_provider_type("offline", DummyOffline)
    factory.register_provider_type("lmstudio", DummyLMStudio)

    provider = factory.create_provider("lmstudio")
    assert isinstance(provider, DummyOffline)
