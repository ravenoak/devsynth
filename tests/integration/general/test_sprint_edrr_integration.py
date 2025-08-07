import pytest

from devsynth.methodology.sprint import SprintAdapter


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

    adapter.after_cycle(results)

    assert adapter.sprint_plan["planned_scope"] == ["feature"]
    assert adapter.metrics["planned_scope"][0] == ["feature"]
    assert adapter.metrics["actual_scope"][0] == ["feature"]


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

    adapter.after_cycle(results)

    assert adapter.metrics["retrospective_reviews"][0]["action_items"] == ["fix"]
    assert adapter.metrics["quality_metrics"][adapter.current_sprint_number] == {
        "quality": "high"
    }
