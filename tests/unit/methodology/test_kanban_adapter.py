import pytest

from devsynth.methodology.base import Phase
from devsynth.methodology.kanban import KanbanAdapter


@pytest.mark.fast
def test_should_start_cycle():
    adapter = KanbanAdapter({"settings": {"wipLimits": {p.value: 1 for p in Phase}}})
    assert adapter.should_start_cycle()


@pytest.mark.fast
def test_progress_respects_wip_limit():
    adapter = KanbanAdapter({"settings": {"wipLimits": {p.value: 1 for p in Phase}}})
    adapter.board_state[Phase.DIFFERENTIATE] = 1
    results = {"phase_complete": True}
    assert not adapter.should_progress_to_next_phase(Phase.EXPAND, {}, results)
    adapter.board_state[Phase.DIFFERENTIATE] = 0
    assert adapter.should_progress_to_next_phase(Phase.EXPAND, {}, results)
