import datetime

import pytest

from devsynth.methodology.base import Phase
from devsynth.methodology.sprint import SprintAdapter


@pytest.mark.fast
def test_calculate_phase_end_time():
    """SprintAdapter calculates phase end time correctly.

    ReqID: FR-88"""
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    start = datetime.datetime(2023, 1, 1)
    end = adapter._calculate_phase_end_time(Phase.EXPAND, start)
    expected_seconds = adapter._calculate_phase_duration_seconds(Phase.EXPAND)
    assert (end - start).total_seconds() == expected_seconds


@pytest.mark.fast
def test_is_phase_time_exceeded_false(monkeypatch):
    """_is_phase_time_exceeded respects allocation.

    ReqID: FR-88"""
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    start = datetime.datetime.now()
    monkeypatch.setattr(datetime, "datetime", datetime.datetime)
    assert not adapter._is_phase_time_exceeded(Phase.EXPAND, start)


@pytest.mark.fast
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


@pytest.mark.fast
def test_ceremony_mapping_to_phase():
    """Configured ceremonies map to the correct EDRR phases."""
    config = {
        "settings": {
            "ceremonyMapping": {
                "planning": "retrospect.iteration_planning",
                "dailyStandup": "phase_progression_tracking",
                "review": "refine.outputs_review",
                "retrospective": "retrospect.process_evaluation",
            }
        }
    }
    adapter = SprintAdapter(config)
    assert adapter.get_ceremony_phase("planning") == Phase.RETROSPECT
    assert adapter.get_ceremony_phase("review") == Phase.REFINE
    assert adapter.get_ceremony_phase("retrospective") == Phase.RETROSPECT
    assert adapter.get_ceremony_phase("dailyStandup") is None


@pytest.mark.fast
def test_before_cycle_provides_context():
    """before_cycle initializes sprint metadata."""
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    context = adapter.before_cycle()
    assert context["sprint_number"] == 1
    assert "sprint_start_time" in context
    assert "sprint_end_time" in context


@pytest.mark.fast
def test_before_expand_sets_phase_start_time():
    """before_expand adds a phase start timestamp."""
    adapter = SprintAdapter({"settings": {}})
    context = adapter.before_expand({})
    assert "phase_start_time" in context
    assert isinstance(context["phase_start_time"], datetime.datetime)


@pytest.mark.fast
def test_after_retrospect_captures_sprint_plan():
    """after_retrospect stores next cycle recommendations as sprint plan."""
    adapter = SprintAdapter({"settings": {}})
    results = {
        "next_cycle_recommendations": {
            "scope": ["item1"],
            "objectives": ["obj"],
            "success_criteria": ["done"],
        }
    }
    adapter.after_retrospect({}, results)
    assert adapter.sprint_plan["planned_scope"] == ["item1"]
    assert adapter.sprint_plan["objectives"] == ["obj"]
    assert adapter.sprint_plan["success_criteria"] == ["done"]
