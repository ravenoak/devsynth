import types
import importlib
import pytest
import httpx

def _mock_config():
    cfg = types.SimpleNamespace()
    cfg.as_dict = lambda: {'offline_mode': True}
    return cfg

def _llm_settings():
    return {'provider': 'openai'}

@pytest.mark.medium
def test_generate_does_not_call_external_succeeds(monkeypatch):
    """Test that generate does not call external succeeds.

    This test needs to be run in isolation due to interactions with other tests.

ReqID: N/A"""
    monkeypatch.setattr('devsynth.core.config_loader.load_config', _mock_config)
    monkeypatch.setattr('devsynth.config.get_llm_settings', _llm_settings)
    llm = importlib.import_module('devsynth.application.llm')
    providers = importlib.import_module('devsynth.application.llm.providers')
    importlib.reload(providers)
    importlib.reload(llm)
    OfflineProvider = importlib.import_module('devsynth.application.llm.offline_provider').OfflineProvider

    def mock_request(*args, **kwargs):
        pytest.fail("External HTTP request was made when it shouldn't have been")
    monkeypatch.setattr(httpx, 'request', mock_request)
    provider = llm.get_llm_provider()
    assert isinstance(provider, OfflineProvider), f'Expected OfflineProvider but got {type(provider)}'
    result = provider.generate('hello')
    assert result == '[offline] hello', f"Expected '[offline] hello' but got '{result}'"