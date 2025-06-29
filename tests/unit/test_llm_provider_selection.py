import types

from devsynth.application.llm import get_llm_provider
from devsynth.application.llm.offline_provider import OfflineProvider
from devsynth.application.llm.openai_provider import OpenAIProvider


def _mock_config(offline: bool):
    cfg = types.SimpleNamespace()
    cfg.config = types.SimpleNamespace()
    cfg.config.as_dict = lambda: {"offline_mode": offline}
    return cfg


def test_offline_mode_selects_offline_provider(monkeypatch):
    monkeypatch.setattr(
        "devsynth.application.utils.token_tracker.TIKTOKEN_AVAILABLE", False
    )
    monkeypatch.setattr(
        "devsynth.application.llm.providers.load_project_config",
        lambda: _mock_config(True),
    )
    monkeypatch.setattr(
        "devsynth.application.llm.providers.get_llm_settings",
        lambda: {
            "provider": "openai",
            "openai_api_key": "key",
            "openai_model": "gpt-3.5-turbo",
        },
    )
    provider = get_llm_provider()
    assert isinstance(provider, OfflineProvider)


def test_online_mode_uses_configured_provider(monkeypatch):
    monkeypatch.setattr(
        "devsynth.application.utils.token_tracker.TIKTOKEN_AVAILABLE", False
    )
    monkeypatch.setattr(
        "devsynth.application.llm.providers.load_project_config",
        lambda: _mock_config(False),
    )
    monkeypatch.setattr(
        "devsynth.application.llm.providers.get_llm_settings",
        lambda: {
            "provider": "openai",
            "openai_api_key": "key",
            "openai_model": "gpt-3.5-turbo",
        },
    )
    provider = get_llm_provider()
    assert isinstance(provider, OpenAIProvider)
