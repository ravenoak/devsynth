import os

import pytest


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_adapter_openai_provider_stub_offline(monkeypatch):
    """
    When DEVSYNTH_OFFLINE=true and normalized stubs are applied (default),
    adapter-level OpenAIProvider should return deterministic responses.
    """
    # Ensure offline and that provider availability flags don't accidentally enable real backend
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "stub")

    # Import locally to ensure stub application via tests/conftest autouse fixture has run
    import devsynth.adapters.provider_system as provider_system  # type: ignore

    p = provider_system.OpenAIProvider()
    assert p.complete("Hello") == "Test completion response"
    assert p.embed("Hello") == [0.1, 0.2, 0.3, 0.4]
