from devsynth.application.llm.offline_provider import OfflineProvider


def test_offline_provider_instantiation() -> None:
    provider = OfflineProvider()
    assert isinstance(provider, OfflineProvider)
    assert provider.generate("hello") == "[offline] hello"
    emb = provider.get_embedding("text")
    assert isinstance(emb, list)
    assert len(emb) == 8
