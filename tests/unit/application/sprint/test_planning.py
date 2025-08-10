"""Tests for sprint planning helpers."""

from devsynth.application.sprint.planning import map_requirements_to_plan


def test_map_requirements_to_plan_extracts_fields() -> None:
    """It maps requirement analysis results to a plan structure."""
    requirements = {
        "recommended_scope": ["feat"],
        "objectives": ["goal"],
        "success_criteria": ["metric"],
    }
    expected = {
        "planned_scope": ["feat"],
        "objectives": ["goal"],
        "success_criteria": ["metric"],
    }
    assert map_requirements_to_plan(requirements) == expected
