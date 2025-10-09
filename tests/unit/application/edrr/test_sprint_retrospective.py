"""Unit tests for sprint retrospective utilities."""

import pytest

from devsynth.application.edrr.sprint_retrospective import (
    SPRINT_RETROSPECTIVE_PHASE,
    map_retrospective_to_summary,
)


class TestSprintRetrospective:
    """Test sprint retrospective utilities."""

    @pytest.mark.fast
    def test_sprint_retrospective_phase_constant(self):
        """Test that SPRINT_RETROSPECTIVE_PHASE has the expected value."""
        assert SPRINT_RETROSPECTIVE_PHASE == "retrospect"

    @pytest.mark.fast
    def test_map_retrospective_to_summary_basic(self):
        """Test basic mapping of retrospective to summary."""
        retrospective = {
            "positives": ["good1", "good2"],
            "improvements": ["improve1"],
            "action_items": ["action1"],
        }
        sprint = 5

        result = map_retrospective_to_summary(retrospective, sprint)

        expected = {
            "positives": ["good1", "good2"],
            "improvements": ["improve1"],
            "action_items": ["action1"],
            "sprint": 5,
        }

        assert result == expected

    @pytest.mark.fast
    def test_map_retrospective_to_summary_empty(self):
        """Test mapping with empty retrospective."""
        retrospective = {}
        sprint = 3

        result = map_retrospective_to_summary(retrospective, sprint)

        assert result == {}

    @pytest.mark.fast
    def test_map_retrospective_to_summary_none(self):
        """Test mapping with None retrospective."""
        retrospective = None
        sprint = 1

        result = map_retrospective_to_summary(retrospective, sprint)

        assert result == {}

    @pytest.mark.fast
    def test_map_retrospective_to_summary_partial(self):
        """Test mapping with partial retrospective data."""
        retrospective = {
            "positives": ["good1"],
            # improvements and action_items missing
        }
        sprint = 7

        result = map_retrospective_to_summary(retrospective, sprint)

        expected = {
            "positives": ["good1"],
            "improvements": [],
            "action_items": [],
            "sprint": 7,
        }

        assert result == expected
