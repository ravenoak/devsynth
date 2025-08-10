from devsynth.methodology.base import Phase
from devsynth.methodology.sprint import SprintAdapter


def test_default_ceremony_mapping_aligns_with_edrr():
    adapter = SprintAdapter(config={})
    assert adapter.get_ceremony_phase("planning") is Phase.EXPAND
    assert adapter.get_ceremony_phase("retrospective") is Phase.RETROSPECT
