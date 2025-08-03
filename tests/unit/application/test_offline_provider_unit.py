import pytest
from devsynth.application.llm.offline_provider import OfflineProvider

@pytest.mark.medium
def test_offline_provider_instantiation_succeeds(tmp_path) -> None:
    """Test that offline provider instantiation succeeds.

ReqID: N/A"""
    provider = OfflineProvider()
    assert isinstance(provider, OfflineProvider)
    assert provider.generate('hello') == '[offline] hello'
    emb = provider.get_embedding('text')
    assert isinstance(emb, list)
    assert len(emb) == 8