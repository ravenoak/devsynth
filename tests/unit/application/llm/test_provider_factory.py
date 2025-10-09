import pytest

from devsynth.application.llm.provider_factory import factory

pytestmark = [pytest.mark.fast]


def test_default_selection_is_deterministic(monkeypatch):
    """Factory should fall back to the next provider in order."""

    class DummyOpenAI:
        def __init__(self, config=None):
            self.config = config

    class DummyAnthropic:
        def __init__(self, config=None):
            self.config = config

    monkeypatch.setattr(
        factory, "provider_types", {"openai": DummyOpenAI, "anthropic": DummyAnthropic}
    )
    monkeypatch.delitem(factory.provider_types, "openai", raising=False)
    provider = factory.create_provider()
    assert isinstance(provider, DummyAnthropic)


def test_case_insensitive_selection(monkeypatch):
    class DummyOpenAI:
        def __init__(self, config=None):
            self.config = config

    monkeypatch.setattr(factory, "provider_types", {"openai": DummyOpenAI})
    provider = factory.create_provider("OPENAI")
    assert isinstance(provider, DummyOpenAI)
