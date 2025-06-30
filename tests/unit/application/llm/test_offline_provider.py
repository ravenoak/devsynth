import types

from devsynth.application.llm import get_llm_provider
from devsynth.application.llm.offline_provider import OfflineProvider


def _mock_config():
    cfg = types.SimpleNamespace()
    cfg.as_dict = lambda: {"offline_mode": True}
    return cfg


def test_get_llm_provider_returns_offline(monkeypatch):
    monkeypatch.setattr(
        "devsynth.application.llm.providers.load_config",
        lambda: _mock_config(),
    )
    monkeypatch.setattr(
        "devsynth.application.llm.providers.get_llm_settings",
        lambda: {"provider": "openai"},
    )

    provider = get_llm_provider()
    assert isinstance(provider, OfflineProvider)
