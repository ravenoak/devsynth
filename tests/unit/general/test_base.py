import pytest

from devsynth.methodology.base import BaseMethodologyAdapter, Phase


class DummyAdapter(BaseMethodologyAdapter):

    def should_start_cycle(self) -> bool:
        return True

    def should_progress_to_next_phase(
        self, current_phase: Phase, context, results
    ) -> bool:
        return False

    def after_cycle(self, results):
        pass


@pytest.mark.fast
def test_dummy_adapter_succeeds():
    """Test that dummy adapter succeeds.

    ReqID: N/A"""
    adapter = DummyAdapter({})
    assert adapter.get_metadata()["name"] == "DummyAdapter"
