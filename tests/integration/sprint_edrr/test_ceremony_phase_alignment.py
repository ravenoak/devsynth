import pytest

from devsynth.methodology.base import Phase
from devsynth.methodology.sprint import SprintAdapter


@pytest.mark.medium
def test_default_ceremony_mapping_aligns_with_edrr():
    adapter = SprintAdapter(config={})
    assert adapter.get_ceremony_phase("planning") is Phase.EXPAND
    assert adapter.get_ceremony_phase("dailyStandup") is Phase.DIFFERENTIATE
    assert adapter.get_ceremony_phase("review") is Phase.REFINE
    assert adapter.get_ceremony_phase("retrospective") is Phase.RETROSPECT
