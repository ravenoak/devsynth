"""Integration tests for provider selection and safe fallbacks.

These tests exercise the selection logic through both:
- devsynth.application.llm.get_llm_provider (thin wrapper around providers.factory)
- devsynth.application.llm.providers.get_llm_provider (stricter validation path)

They ensure:
- Offline mode selects OfflineProvider without needing credentials
- Requesting a remote provider (OpenAI) without credentials fails fast with
  a clear, typed exception, and without performing network I/O

Style: Deterministic, no network, explicit markers, aligns with project guidelines
and docs/tasks.md (5.41).
"""

from __future__ import annotations

import os
import types

import pytest

# Public wrapper path
from devsynth.application import llm as app_llm

# Stricter provider selection path
from devsynth.application.llm import providers as prov
from devsynth.application.llm.openai_provider import OpenAIConnectionError
from devsynth.application.llm.providers import OfflineProvider, ValidationError

pytestmark = [pytest.mark.integration, pytest.mark.no_network]


def _mock_config(offline: bool, offline_provider: str | None = None):
    cfg = types.SimpleNamespace()

    def as_dict():
        d = {"offline_mode": offline}
        if offline_provider is not None:
            d["offline_provider"] = offline_provider
        return d

    cfg.as_dict = as_dict
    return cfg


def _llm_settings(provider: str):
    # Minimal llm settings used by selection logic
    return {"provider": provider}


@pytest.mark.medium
def test_offline_mode_returns_offline_provider_for_app_wrapper(monkeypatch):
    """application.llm.get_llm_provider selects OfflineProvider when offline_mode is True."""
    monkeypatch.setattr(app_llm, "load_config", lambda: _mock_config(True, "local"))
    monkeypatch.setattr(app_llm, "get_llm_settings", lambda: _llm_settings("openai"))

    provider = app_llm.get_llm_provider()
    assert isinstance(provider, OfflineProvider)


@pytest.mark.medium
def test_offline_mode_returns_offline_provider_for_providers_module(monkeypatch):
    """providers.get_llm_provider selects 'offline' when offline_mode is True."""
    monkeypatch.setattr(prov, "load_config", lambda: _mock_config(True, "local"))
    monkeypatch.setattr(prov, "get_llm_settings", lambda: _llm_settings("openai"))

    provider = prov.get_llm_provider()
    assert isinstance(provider, OfflineProvider)


@pytest.mark.medium
def test_openai_without_api_key_raises_validation_error_in_providers(monkeypatch):
    """Requesting OpenAI without credentials should fail fast in providers.get_llm_provider.

    This path validates credentials before constructing the provider class.
    """
    # Ensure no OPENAI_API_KEY in environment for this test
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    monkeypatch.setattr(prov, "load_config", lambda: _mock_config(False))
    # get_llm_settings returns no explicit api_key
    monkeypatch.setattr(prov, "get_llm_settings", lambda: {"provider": "openai"})

    with pytest.raises(ValidationError):
        prov.get_llm_provider()


@pytest.mark.medium
def test_openai_without_api_key_raises_connection_error_in_app_wrapper(monkeypatch):
    """application.llm.get_llm_provider constructs the OpenAIProvider which raises OpenAIConnectionError
    when no API key is configured. This still avoids any network calls in tests.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    monkeypatch.setattr(app_llm, "load_config", lambda: _mock_config(False))
    # application.llm.get_llm_provider pulls settings via get_llm_settings()
    monkeypatch.setattr(app_llm, "get_llm_settings", lambda: {"provider": "openai"})

    with pytest.raises(OpenAIConnectionError):
        app_llm.get_llm_provider()
