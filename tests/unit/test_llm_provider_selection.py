import types
from devsynth.application.llm import get_llm_provider
# Import the provider from the same module used by ``get_llm_provider`` to
# avoid type mismatches if ``offline_provider`` is reloaded in other tests.
from devsynth.application.llm.providers import OfflineProvider
from devsynth.application.llm.openai_provider import OpenAIProvider


def _mock_config(offline: bool):
    cfg = types.SimpleNamespace()
    cfg.as_dict = lambda : {'offline_mode': offline}
    return cfg


def test_offline_mode_selects_offline_provider_succeeds(monkeypatch):
    """Test that offline mode selects offline provider succeeds.

ReqID: N/A"""
    monkeypatch.setattr(
        'devsynth.application.utils.token_tracker.TIKTOKEN_AVAILABLE', False)
    monkeypatch.setattr('devsynth.application.llm.load_config', lambda :
        _mock_config(True))
    monkeypatch.setattr('devsynth.application.llm.get_llm_settings', lambda :
        {'provider': 'openai', 'openai_api_key': 'key', 'openai_model':
        'gpt-3.5-turbo'})
    provider = get_llm_provider()
    assert isinstance(provider, OfflineProvider)


def test_online_mode_uses_configured_provider_succeeds(monkeypatch):
    """Test that online mode uses configured provider succeeds.

ReqID: N/A"""
    monkeypatch.setattr(
        'devsynth.application.utils.token_tracker.TIKTOKEN_AVAILABLE', False)
    monkeypatch.setattr('devsynth.application.llm.load_config', lambda :
        _mock_config(False))
    monkeypatch.setattr('devsynth.application.llm.get_llm_settings', lambda :
        {'provider': 'openai', 'openai_api_key': 'key', 'openai_model':
        'gpt-3.5-turbo'})
    provider = get_llm_provider()
    assert isinstance(provider, OpenAIProvider)
