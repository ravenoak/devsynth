import pytest

from devsynth.application.sprint.planning import SPRINT_PLANNING_PHASE
from devsynth.application.sprint.retrospective import SPRINT_RETROSPECTIVE_PHASE
from devsynth.methodology.base import Phase
from devsynth.methodology.sprint import SprintAdapter


@pytest.mark.slow
def test_requirements_analysis_updates_sprint_plan():
    """SprintAdapter aligns planning with requirement analysis results."""
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    adapter.before_cycle()

    results = {
        "expand": {
            "processed_artifacts": ["feature"],
            "requirements_analysis": {
                "recommended_scope": ["feature"],
                "objectives": ["obj"],
                "success_criteria": ["done"],
            },
        },
        "retrospect": {},
    }

    adapter.after_expand({}, results["expand"])
    adapter.after_cycle(results)

    assert adapter.sprint_plan["planned_scope"] == ["feature"]
    assert adapter.sprint_plan["objectives"] == ["obj"]
    assert adapter.metrics["planned_scope"][0] == ["feature"]
    assert adapter.metrics["actual_scope"][0] == ["feature"]


@pytest.mark.slow
def test_sprint_ceremonies_mapped_to_edrr_phases():
    """Sprint ceremonies align with their corresponding EDRR phases."""
    assert SPRINT_PLANNING_PHASE == Phase.EXPAND.value
    assert SPRINT_RETROSPECTIVE_PHASE == Phase.RETROSPECT.value


@pytest.mark.slow
def test_retrospective_evaluation_logged():
    """Retrospective evaluations are captured in sprint metrics."""
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    adapter.before_cycle()

    retro_results = {
        "positives": ["good"],
        "improvements": ["better"],
        "action_items": ["fix"],
        "evaluation": {"quality": "high"},
    }
    results = {"expand": {}, "retrospect": retro_results}

    adapter.after_retrospect({}, retro_results)
    adapter.after_cycle(results)

    assert adapter.metrics["retrospective_reviews"][0]["action_items"] == ["fix"]
    assert (
        adapter.metrics["retrospective_reviews"][0]["sprint"]
        == adapter.current_sprint_number
    )
    assert adapter.metrics["quality_metrics"][adapter.current_sprint_number] == {
        "quality": "high"
    }
