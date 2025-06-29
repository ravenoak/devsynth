from devsynth.application.llm.offline_provider import OfflineProvider


def test_offline_provider_instantiation() -> None:
    provider = OfflineProvider()
    assert isinstance(provider, OfflineProvider)
