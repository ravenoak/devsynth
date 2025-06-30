import types

import httpx
from devsynth.application.llm import get_llm_provider
from devsynth.application.llm.offline_provider import OfflineProvider


def _mock_config():
    cfg = types.SimpleNamespace()
    cfg.as_dict = lambda: {"offline_mode": True}
    return cfg


def _llm_settings():
    return {"provider": "openai"}


def test_generate_does_not_call_external(monkeypatch):
    called = {}

    def fake_post(*args, **kwargs):
        called["called"] = True
        raise AssertionError("external call")

    monkeypatch.setattr("devsynth.application.llm.load_config", _mock_config)
    monkeypatch.setattr("devsynth.application.llm.get_llm_settings", _llm_settings)
    monkeypatch.setattr(httpx, "post", fake_post)

    provider = get_llm_provider()
    assert isinstance(provider, OfflineProvider)

    result = provider.generate("hello")

    assert result == "[offline] hello"
    assert "called" not in called
