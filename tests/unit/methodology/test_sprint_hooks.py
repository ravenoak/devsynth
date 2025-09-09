import pytest

from devsynth.methodology.base import Phase
from devsynth.methodology.sprint import SprintAdapter
from devsynth.methodology.sprint_adapter import map_ceremony_to_phase


@pytest.mark.fast
def test_map_ceremony_to_phase_defaults():
    """Common ceremonies resolve to their default EDRR phases."""
    assert map_ceremony_to_phase("planning") == Phase.RETROSPECT
    assert map_ceremony_to_phase("review") == Phase.REFINE
    assert map_ceremony_to_phase("retrospective") == Phase.RETROSPECT
    assert map_ceremony_to_phase("dailyStandup") is None
    assert map_ceremony_to_phase("unknown") is None


@pytest.mark.fast
def test_adapter_uses_ceremony_defaults():
    """SprintAdapter falls back to default phase mapping for bare ceremony names."""
    config = {
        "settings": {
            "ceremonyMapping": {
                "planning": "planning",
                "review": "review",
                "retrospective": "retrospective",
            }
        }
    }
    adapter = SprintAdapter(config)
    assert adapter.get_ceremony_phase("planning") == Phase.RETROSPECT
    assert adapter.get_ceremony_phase("review") == Phase.REFINE
    assert adapter.get_ceremony_phase("retrospective") == Phase.RETROSPECT
    assert adapter.get_ceremony_phase("dailyStandup") is None
