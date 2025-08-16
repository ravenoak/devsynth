import types

import pytest

from devsynth.application.llm import providers


class DummyFactory:
    def __init__(self):
        self.calls = []

    def create_provider(self, provider_type, config):
        self.calls.append((provider_type, config))
        return provider_type


@pytest.mark.fast
def test_get_llm_provider_offline(monkeypatch):
    """Selects offline provider when offline mode is enabled.

    ReqID: FR-85"""
    dummy = DummyFactory()
    monkeypatch.setattr(providers, "factory", dummy)
    monkeypatch.setattr(
        providers,
        "load_config",
        lambda: types.SimpleNamespace(
            as_dict=lambda: {"offline_mode": True, "offline_provider": "local"}
        ),
    )
    monkeypatch.setattr(providers, "get_llm_settings", lambda: {"provider": "openai"})
    provider = providers.get_llm_provider()
    assert provider == "offline"
    assert dummy.calls == [
        ("offline", {"provider": "openai", "offline_provider": "local"})
    ]


@pytest.mark.fast
def test_get_llm_provider_default(monkeypatch):
    """Uses configured provider when offline mode is disabled.

    ReqID: FR-85"""
    dummy = DummyFactory()
    monkeypatch.setattr(providers, "factory", dummy)
    monkeypatch.setattr(
        providers, "load_config", lambda: types.SimpleNamespace(as_dict=lambda: {})
    )
    monkeypatch.setattr(providers, "get_llm_settings", lambda: {"provider": "local"})
    provider = providers.get_llm_provider()
    assert provider == "local"
    assert dummy.calls == [("local", {"provider": "local"})]
