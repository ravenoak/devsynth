import importlib

import pytest

from devsynth import config


@pytest.mark.fast
def test_configure_llm_settings_reads_env(monkeypatch):
    """Environment variables update LLM settings when configured."""
    monkeypatch.setenv("DEVSYNTH_LLM_MODEL", "foo-model")
    monkeypatch.setenv("DEVSYNTH_LLM_MAX_TOKENS", "123")
    monkeypatch.setenv("DEVSYNTH_LLM_TEMPERATURE", "0.9")
    monkeypatch.setenv("DEVSYNTH_LLM_AUTO_SELECT_MODEL", "false")

    importlib.reload(config)
    config.configure_llm_settings()

    assert config.LLM_MODEL == "foo-model"
    assert config.LLM_MAX_TOKENS == 123
    assert config.LLM_TEMPERATURE == 0.9
    assert config.LLM_AUTO_SELECT_MODEL is False
