import datetime

from devsynth.methodology.adhoc import AdHocAdapter
from devsynth.methodology.base import Phase


def test_should_start_cycle_true():
    """AdHocAdapter begins a cycle when requested.

    ReqID: FR-88"""
    adapter = AdHocAdapter({"settings": {"startNewCycle": True}})
    assert adapter.should_start_cycle()


def test_should_progress_to_next_phase():
    """Progresses when user marks phase complete and requests progression.

    ReqID: FR-88"""
    adapter = AdHocAdapter({"settings": {}})
    context = {"progress_to_next": True}
    results = {"phase_complete": True}
    assert adapter.should_progress_to_next_phase(Phase.EXPAND, context, results)
