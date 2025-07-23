import datetime

from devsynth.methodology.sprint import SprintAdapter
from devsynth.methodology.base import Phase


def test_calculate_phase_end_time():
    """SprintAdapter calculates phase end time correctly.

    ReqID: FR-88"""
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    start = datetime.datetime(2023, 1, 1)
    end = adapter._calculate_phase_end_time(Phase.EXPAND, start)
    expected_seconds = adapter._calculate_phase_duration_seconds(Phase.EXPAND)
    assert (end - start).total_seconds() == expected_seconds


def test_is_phase_time_exceeded_false(monkeypatch):
    """_is_phase_time_exceeded respects allocation.

    ReqID: FR-88"""
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    start = datetime.datetime.now()
    monkeypatch.setattr(datetime, "datetime", datetime.datetime)
    assert not adapter._is_phase_time_exceeded(Phase.EXPAND, start)


def test_should_progress_when_time_exceeded(monkeypatch):
    """should_progress_to_next_phase triggers when time is exceeded.

    ReqID: FR-88"""
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    start = datetime.datetime.now() - datetime.timedelta(days=8)
    adapter.sprint_start_time = start
    context = {"phase_start_time": start}
    results = {"completed_activities": []}
    monkeypatch.setattr(adapter, "_get_required_activities", lambda phase: [])
    assert adapter.should_progress_to_next_phase(Phase.EXPAND, context, results)
