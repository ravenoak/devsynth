import pytest

from devsynth.methodology.base import Phase
from devsynth.methodology.sprint import SprintAdapter


@pytest.mark.medium
def test_sprint_adapter_phase_hooks():
    """SprintAdapter processes EDRR cycle hooks for all phases.

    ReqID: FR-88
    """
    adapter = SprintAdapter({"settings": {"sprintDuration": 1}})
    context = adapter.before_cycle()

    expand_ctx = adapter.before_phase(Phase.EXPAND, context)
    expand_results = adapter.after_phase(
        Phase.EXPAND,
        expand_ctx,
        {
            "requirements_analysis": {},
            "processed_artifacts": ["a"],
            "completed_activities": [
                "discovery_complete",
                "classification_complete",
                "extraction_complete",
            ],
        },
    )

    diff_ctx = adapter.before_phase(Phase.DIFFERENTIATE, context)
    assert "phase_start_time" in diff_ctx
    diff_results = adapter.after_phase(
        Phase.DIFFERENTIATE,
        diff_ctx,
        {
            "inconsistencies": ["gap"],
            "completed_activities": ["validation_complete", "gap_analysis_complete"],
        },
    )
    assert adapter.metrics["inconsistencies_detected"][-1] == ["gap"]

    refine_ctx = adapter.before_phase(Phase.REFINE, context)
    assert "phase_start_time" in refine_ctx
    refine_results = adapter.after_phase(
        Phase.REFINE,
        refine_ctx,
        {
            "relationships": ["rel"],
            "completed_activities": [
                "context_merging_complete",
                "relationship_modeling_complete",
            ],
        },
    )
    assert adapter.metrics["relationships_modeled"][-1] == ["rel"]

    retro_ctx = adapter.before_phase(Phase.RETROSPECT, context)
    assert "phase_start_time" in retro_ctx
    retro_results = adapter.after_phase(
        Phase.RETROSPECT,
        retro_ctx,
        {
            "insights": ["improve"],
            "evaluation": {"score": 1},
            "next_cycle_recommendations": {
                "scope": [],
                "objectives": [],
                "success_criteria": [],
            },
            "completed_activities": [
                "evaluation_complete",
                "insight_capture_complete",
                "planning_complete",
            ],
        },
    )

    cycle_results = {
        "expand": expand_results,
        "differentiate": diff_results,
        "refine": refine_results,
        "retrospect": retro_results,
    }
    adapter.after_cycle(cycle_results)
    assert adapter.metrics["velocity"][-1]["completed_items"] == 1
