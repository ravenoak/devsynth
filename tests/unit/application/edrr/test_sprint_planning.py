"""Unit tests for sprint planning utilities."""

import pytest

from devsynth.application.edrr.sprint_planning import (
    SPRINT_PLANNING_PHASE,
    map_requirements_to_plan,
)


class TestSprintPlanning:
    """Test sprint planning utilities."""

    @pytest.mark.fast
    def test_sprint_planning_phase_constant(self):
        """Test that SPRINT_PLANNING_PHASE has the expected value."""
        assert SPRINT_PLANNING_PHASE == "expand"

    @pytest.mark.fast
    def test_map_requirements_to_plan_basic(self):
        """Test basic mapping of requirements to sprint plan."""
        requirement_results = {
            "recommended_scope": ["feature1", "feature2"],
            "objectives": ["objective1"],
            "success_criteria": ["criteria1"],
        }

        result = map_requirements_to_plan(requirement_results)

        expected = {
            "planned_scope": ["feature1", "feature2"],
            "objectives": ["objective1"],
            "success_criteria": ["criteria1"],
        }

        assert result == expected

    @pytest.mark.fast
    def test_map_requirements_to_plan_empty(self):
        """Test mapping with empty requirement results."""
        requirement_results = {}

        result = map_requirements_to_plan(requirement_results)

        expected = {
            "planned_scope": [],
            "objectives": [],
            "success_criteria": [],
        }

        assert result == expected

    @pytest.mark.fast
    def test_map_requirements_to_plan_partial(self):
        """Test mapping with partial requirement results."""
        requirement_results = {
            "recommended_scope": ["feature1"],
            # objectives and success_criteria missing
        }

        result = map_requirements_to_plan(requirement_results)

        expected = {
            "planned_scope": ["feature1"],
            "objectives": [],
            "success_criteria": [],
        }

        assert result == expected
