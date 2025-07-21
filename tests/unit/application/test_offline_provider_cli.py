import types
import importlib
import pytest
import httpx


def _mock_config():
    cfg = types.SimpleNamespace()
    cfg.as_dict = lambda : {'offline_mode': True}
    return cfg


def _llm_settings():
    return {'provider': 'openai'}


@pytest.mark.isolation
def test_generate_does_not_call_external_succeeds(monkeypatch):
    """Test that generate does not call external succeeds.

    This test needs to be run in isolation due to interactions with other tests.

ReqID: N/A"""
    # Patch configuration helpers before importing modules that read them
    monkeypatch.setattr('devsynth.core.config_loader.load_config', _mock_config)
    monkeypatch.setattr('devsynth.config.get_llm_settings', _llm_settings)

    # Import and reload modules to ensure patches are used
    llm = importlib.import_module('devsynth.application.llm')
    providers = importlib.import_module('devsynth.application.llm.providers')
    importlib.reload(providers)
    importlib.reload(llm)
    OfflineProvider = importlib.import_module(
        'devsynth.application.llm.offline_provider'
    ).OfflineProvider

    # Mock httpx to ensure no external calls are made
    def mock_request(*args, **kwargs):
        pytest.fail("External HTTP request was made when it shouldn't have been")

    monkeypatch.setattr(httpx, 'request', mock_request)

    # Get the provider and verify it's an OfflineProvider
    provider = llm.get_llm_provider()
    assert isinstance(provider, OfflineProvider), (
        f"Expected OfflineProvider but got {type(provider)}"
    )

    # Generate text and verify the result
    result = provider.generate('hello')
    assert result == '[offline] hello', f"Expected '[offline] hello' but got '{result}'"

    # The test passes if we get here without any exceptions
    # The OfflineProvider should not make any external calls
