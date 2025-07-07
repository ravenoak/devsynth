"""
Unit tests for enhanced EDRR phase transitions.

This module contains unit tests for the enhanced phase transition functionality
in the EDRR framework, including quality scoring, metrics collection, and
automatic phase transitions.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from devsynth.application.edrr.edrr_phase_transitions import (
    PhaseTransitionMetrics, calculate_enhanced_quality_score, collect_phase_metrics,
    QualityThreshold, MetricType
)
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.methodology.base import Phase


class TestPhaseTransitionMetrics:
    """Test suite for PhaseTransitionMetrics class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.metrics = PhaseTransitionMetrics()

    def test_start_phase(self):
        """Test recording the start of a phase."""
        # Act
        self.metrics.start_phase(Phase.EXPAND)

        # Assert
        assert Phase.EXPAND.name in self.metrics.start_times
        assert len(self.metrics.history) == 1
        assert self.metrics.history[0]["phase"] == Phase.EXPAND.name
        assert self.metrics.history[0]["action"] == "start"

    def test_end_phase(self):
        """Test recording the end of a phase with metrics."""
        # Arrange
        self.metrics.start_phase(Phase.EXPAND)
        test_metrics = {
            "quality": 0.8,
            "completeness": 0.7,
            "consistency": 0.9,
            "conflicts": 0
        }

        # Act
        self.metrics.end_phase(Phase.EXPAND, test_metrics)

        # Assert
        assert Phase.EXPAND.name in self.metrics.metrics
        assert self.metrics.metrics[Phase.EXPAND.name] == test_metrics
        assert len(self.metrics.history) == 2
        assert self.metrics.history[1]["phase"] == Phase.EXPAND.name
        assert self.metrics.history[1]["action"] == "end"
        assert self.metrics.history[1]["metrics"] == test_metrics

    def test_should_transition_all_thresholds_met(self):
        """Test should_transition when all thresholds are met."""
        # Arrange
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1  # Below the threshold of 3
        }
        self.metrics.metrics[phase.name] = metrics

        # Act
        should_transition, reasons = self.metrics.should_transition(phase)

        # Assert
        assert should_transition is True
        assert all("Meets threshold" in reason or "within threshold" in reason for reason in reasons.values())

    def test_should_transition_some_thresholds_not_met(self):
        """Test should_transition when some thresholds are not met."""
        # Arrange
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.1,  # Below threshold
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1
        }
        self.metrics.metrics[phase.name] = metrics

        # Act
        should_transition, reasons = self.metrics.should_transition(phase)

        # Assert
        assert should_transition is False
        assert "Below threshold" in reasons[MetricType.QUALITY.value]

    def test_should_transition_missing_metrics(self):
        """Test should_transition when metrics are missing."""
        # Arrange
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value + 0.1,
            # Missing COMPLETENESS
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1
        }
        self.metrics.metrics[phase.name] = metrics

        # Act
        should_transition, reasons = self.metrics.should_transition(phase)

        # Assert
        assert should_transition is False
        assert "Missing metric" in reasons[MetricType.COMPLETENESS.value]

    def test_should_transition_too_many_conflicts(self):
        """Test should_transition when there are too many conflicts."""
        # Arrange
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 5  # Above the threshold of 3
        }
        self.metrics.metrics[phase.name] = metrics

        # Act
        should_transition, reasons = self.metrics.should_transition(phase)

        # Assert
        assert should_transition is False
        assert "Too many conflicts" in reasons[MetricType.CONFLICTS.value]


class TestQualityScoring:
    """Test suite for quality scoring functions."""

    def test_calculate_enhanced_quality_score_non_dict(self):
        """Test calculating quality score for non-dictionary results."""
        # Arrange
        result = "This is a string result"

        # Act
        score = calculate_enhanced_quality_score(result)

        # Assert
        assert score == 0.5  # Default score for non-dictionary results

    def test_calculate_enhanced_quality_score_empty_dict(self):
        """Test calculating quality score for empty dictionary results."""
        # Arrange
        result = {}

        # Act
        score = calculate_enhanced_quality_score(result)

        # Assert
        assert score > 0  # Should still return a score
        assert score < 0.5  # But it should be low due to lack of content

    def test_calculate_enhanced_quality_score_good_result(self):
        """Test calculating quality score for a good result."""
        # Arrange
        result = {
            "description": "A comprehensive solution",
            "approach": "Using best practices",
            "implementation": "Detailed implementation steps",
            "analysis": "Thorough analysis of the solution",
            "solution": "Complete solution with error handling",
            "quality_score": 0.9  # Explicit quality score
        }

        # Act
        score = calculate_enhanced_quality_score(result)

        # Assert
        assert score > 0.7  # Should be a high score

    def test_calculate_enhanced_quality_score_with_errors(self):
        """Test calculating quality score for a result with errors."""
        # Arrange
        result = {
            "description": "A solution with issues",
            "approach": "Using some practices",
            "implementation": "Implementation steps",
            "error": "There was an error in the implementation"
        }

        # Act
        score = calculate_enhanced_quality_score(result)

        # Assert
        assert score < 0.7  # Should be a lower score due to errors

    def test_collect_phase_metrics_expand_phase(self):
        """Test collecting metrics for the Expand phase."""
        # Arrange
        results = {
            "result1": {
                "ideas": ["Idea 1", "Idea 2", "Idea 3"],
                "quality_score": 0.8
            },
            "result2": {
                "approaches": ["Approach 1", "Approach 2"],
                "quality_score": 0.7
            }
        }

        # Act
        metrics = collect_phase_metrics(Phase.EXPAND, results)

        # Assert
        assert MetricType.QUALITY.value in metrics
        assert MetricType.COMPLETENESS.value in metrics
        assert MetricType.CONSISTENCY.value in metrics
        assert MetricType.CONFLICTS.value in metrics
        assert "idea_diversity" in metrics

    def test_collect_phase_metrics_differentiate_phase(self):
        """Test collecting metrics for the Differentiate phase."""
        # Arrange
        results = {
            "result1": {
                "categories": {
                    "category1": ["Item 1", "Item 2"],
                    "category2": ["Item 3", "Item 4"]
                },
                "quality_score": 0.8
            }
        }

        # Act
        metrics = collect_phase_metrics(Phase.DIFFERENTIATE, results)

        # Assert
        assert MetricType.QUALITY.value in metrics
        assert MetricType.COMPLETENESS.value in metrics
        assert MetricType.CONSISTENCY.value in metrics
        assert MetricType.CONFLICTS.value in metrics
        assert "categorization_quality" in metrics

    def test_collect_phase_metrics_refine_phase(self):
        """Test collecting metrics for the Refine phase."""
        # Arrange
        results = {
            "result1": {
                "code": """
                def test_function():
                    # This is a comment
                    try:
                        return "Hello, world!"
                    except Exception as e:
                        return str(e)
                """,
                "test_coverage": 80,
                "quality_score": 0.8
            }
        }

        # Act
        metrics = collect_phase_metrics(Phase.REFINE, results)

        # Assert
        assert MetricType.QUALITY.value in metrics
        assert MetricType.COMPLETENESS.value in metrics
        assert MetricType.CONSISTENCY.value in metrics
        assert MetricType.CONFLICTS.value in metrics
        assert MetricType.COVERAGE.value in metrics
        assert "code_quality" in metrics

    def test_collect_phase_metrics_retrospect_phase(self):
        """Test collecting metrics for the Retrospect phase."""
        # Arrange
        results = {
            "result1": {
                "learnings": ["Learning 1", "Learning 2"],
                "improvements": ["Improvement 1", "Improvement 2"],
                "successes": ["Success 1", "Success 2"],
                "challenges": ["Challenge 1", "Challenge 2"],
                "next_steps": ["Next step 1", "Next step 2"],
                "quality_score": 0.9
            }
        }

        # Act
        metrics = collect_phase_metrics(Phase.RETROSPECT, results)

        # Assert
        assert MetricType.QUALITY.value in metrics
        assert MetricType.COMPLETENESS.value in metrics
        assert MetricType.CONSISTENCY.value in metrics
        assert MetricType.CONFLICTS.value in metrics
        assert "retrospective_quality" in metrics


@pytest.fixture
def mock_coordinator():
    """Create a mock EnhancedEDRRCoordinator for testing."""
    coordinator = MagicMock(spec=EnhancedEDRRCoordinator)
    coordinator.current_phase = Phase.EXPAND
    coordinator.results = {
        Phase.EXPAND.name: {
            "result1": {
                "ideas": ["Idea 1", "Idea 2"],
                "quality_score": 0.8
            }
        }
    }
    coordinator.phase_metrics = PhaseTransitionMetrics()
    coordinator._phase_start_times = {
        Phase.EXPAND: datetime.now() - timedelta(hours=1)
    }
    coordinator.auto_phase_transitions = True
    coordinator.quality_based_transitions = True
    coordinator.phase_transition_timeout = 3600

    return coordinator


class TestEnhancedEDRRCoordinator:
    """Test suite for EnhancedEDRRCoordinator class."""

    @patch('devsynth.application.edrr.edrr_coordinator_enhanced.collect_phase_metrics')
    def test_progress_to_phase_collects_metrics(self, mock_collect_metrics, mock_coordinator):
        """Test that progress_to_phase collects metrics."""
        # Arrange
        mock_collect_metrics.return_value = {
            "quality": 0.8,
            "completeness": 0.7,
            "consistency": 0.9,
            "conflicts": 0
        }

        # Mock all the necessary methods and attributes
        mock_coordinator.progress_to_phase = EnhancedEDRRCoordinator.progress_to_phase.__get__(mock_coordinator)
        mock_coordinator._safe_store_with_edrr_phase = MagicMock()
        mock_coordinator._enhanced_maybe_auto_progress = MagicMock()
        mock_coordinator.phase_metrics = MagicMock()
        mock_coordinator.phase_metrics.start_phase = MagicMock()
        mock_coordinator.phase_metrics.end_phase = MagicMock()
        mock_coordinator.results = {Phase.DIFFERENTIATE.name: {}}
        mock_coordinator.cycle_id = "test_cycle_id"

        # Act
        with patch('devsynth.application.edrr.edrr_coordinator_enhanced.super') as mock_super:
            mock_super.return_value.progress_to_phase = MagicMock()
            # Use try-except to catch and print any exceptions for debugging
            try:
                mock_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
            except Exception as e:
                print(f"Exception in test_progress_to_phase_collects_metrics: {e}")
                raise

        # Assert
        mock_collect_metrics.assert_called_once()
        mock_coordinator.phase_metrics.start_phase.assert_called_once_with(Phase.DIFFERENTIATE)
        mock_coordinator.phase_metrics.end_phase.assert_called_once()
        mock_coordinator._safe_store_with_edrr_phase.assert_called_once()
        mock_coordinator._enhanced_maybe_auto_progress.assert_called_once()

    def test_enhanced_decide_next_phase_quality_based(self, mock_coordinator):
        """Test that _enhanced_decide_next_phase considers quality metrics."""
        # Arrange
        mock_coordinator._enhanced_decide_next_phase = EnhancedEDRRCoordinator._enhanced_decide_next_phase.__get__(mock_coordinator)

        # Set up phase metrics to indicate transition should occur
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1
        }
        mock_coordinator.phase_metrics.metrics[Phase.EXPAND.name] = metrics

        # Act
        next_phase = mock_coordinator._enhanced_decide_next_phase()

        # Assert
        assert next_phase == Phase.DIFFERENTIATE

    def test_enhanced_decide_next_phase_timeout_based(self, mock_coordinator):
        """Test that _enhanced_decide_next_phase considers timeouts."""
        # Arrange
        mock_coordinator._enhanced_decide_next_phase = EnhancedEDRRCoordinator._enhanced_decide_next_phase.__get__(mock_coordinator)

        # Set up phase metrics to indicate transition should NOT occur based on quality
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.1,  # Below threshold
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value - 0.1,  # Below threshold
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value - 0.1,  # Below threshold
            MetricType.CONFLICTS.value: 4  # Above threshold
        }
        mock_coordinator.phase_metrics.metrics[Phase.EXPAND.name] = metrics

        # Set timeout to a very small value to trigger timeout-based transition
        mock_coordinator.phase_transition_timeout = 1  # 1 second

        # Act
        next_phase = mock_coordinator._enhanced_decide_next_phase()

        # Assert
        assert next_phase == Phase.DIFFERENTIATE

    def test_enhanced_decide_next_phase_no_transition(self, mock_coordinator):
        """Test that _enhanced_decide_next_phase returns None when no transition should occur."""
        # Arrange
        mock_coordinator._enhanced_decide_next_phase = EnhancedEDRRCoordinator._enhanced_decide_next_phase.__get__(mock_coordinator)

        # Set up phase metrics to indicate transition should NOT occur
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.1,  # Below threshold
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value - 0.1,  # Below threshold
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value - 0.1,  # Below threshold
            MetricType.CONFLICTS.value: 4  # Above threshold
        }
        mock_coordinator.phase_metrics.metrics[Phase.EXPAND.name] = metrics

        # Set a very long timeout to prevent timeout-based transition
        mock_coordinator.phase_transition_timeout = 86400  # 24 hours
        mock_coordinator._phase_start_times[Phase.EXPAND] = datetime.now()  # Just started

        # Act
        next_phase = mock_coordinator._enhanced_decide_next_phase()

        # Assert
        assert next_phase is None

    def test_enhanced_maybe_auto_progress(self, mock_coordinator):
        """Test that _enhanced_maybe_auto_progress calls progress_to_phase when conditions are met and has safeguards against infinite loops."""
        # Arrange
        mock_coordinator._enhanced_maybe_auto_progress = EnhancedEDRRCoordinator._enhanced_maybe_auto_progress.__get__(mock_coordinator)

        # Set up mock to return a value once, then None to simulate a single phase transition
        mock_decide_next = MagicMock()
        mock_decide_next.side_effect = [Phase.DIFFERENTIATE, None]
        mock_coordinator._enhanced_decide_next_phase = mock_decide_next

        # Set up other mocks
        mock_coordinator.auto_phase_transitions = True
        mock_coordinator.current_phase = Phase.EXPAND
        mock_coordinator.results = {}
        mock_coordinator.phase_metrics = MagicMock()

        # Mock the super().progress_to_phase method
        with patch('devsynth.application.edrr.edrr_coordinator_enhanced.EDRRCoordinator.progress_to_phase') as mock_super_progress:
            # Act
            mock_coordinator._enhanced_maybe_auto_progress()

            # Assert
            # Should be called twice: once returning Phase.DIFFERENTIATE, once returning None
            assert mock_coordinator._enhanced_decide_next_phase.call_count == 2
            mock_super_progress.assert_called_once_with(Phase.DIFFERENTIATE)

            # Verify the guard flag is cleared after execution
            assert not getattr(mock_coordinator, '_in_auto_progress', False)

    def test_enhanced_maybe_auto_progress_reentry_prevention(self, mock_coordinator):
        """Test that _enhanced_maybe_auto_progress prevents re-entry during active transition."""
        # Arrange
        mock_coordinator._enhanced_maybe_auto_progress = EnhancedEDRRCoordinator._enhanced_maybe_auto_progress.__get__(mock_coordinator)
        mock_coordinator._enhanced_decide_next_phase = MagicMock(return_value=Phase.DIFFERENTIATE)

        # Simulate already being in auto-progress
        mock_coordinator._in_auto_progress = True

        # Act
        mock_coordinator._enhanced_maybe_auto_progress()

        # Assert - should not call _enhanced_decide_next_phase due to guard
        mock_coordinator._enhanced_decide_next_phase.assert_not_called()

    def test_enhanced_maybe_auto_progress_max_iterations(self, mock_coordinator):
        """Test that _enhanced_maybe_auto_progress respects maximum iteration count."""
        # Arrange
        mock_coordinator._enhanced_maybe_auto_progress = EnhancedEDRRCoordinator._enhanced_maybe_auto_progress.__get__(mock_coordinator)

        # Always return the next phase to simulate potential infinite loop
        mock_coordinator._enhanced_decide_next_phase = MagicMock(return_value=Phase.DIFFERENTIATE)

        # Mock the super().progress_to_phase method
        with patch('devsynth.application.edrr.edrr_coordinator_enhanced.EDRRCoordinator.progress_to_phase') as mock_super_progress:
            # Mock phase_metrics to avoid errors
            mock_coordinator.phase_metrics = MagicMock()
            mock_coordinator.phase_metrics.end_phase = MagicMock()
            mock_coordinator.results = {}

            # Act
            mock_coordinator._enhanced_maybe_auto_progress()

            # Assert - should stop after max_iterations (4)
            assert mock_coordinator._enhanced_decide_next_phase.call_count <= 4
            assert mock_super_progress.call_count <= 4

    def test_calculate_quality_score(self, mock_coordinator):
        """Test that _calculate_quality_score uses the enhanced quality scoring."""
        # Arrange
        mock_coordinator._calculate_quality_score = EnhancedEDRRCoordinator._calculate_quality_score.__get__(mock_coordinator)
        result = {
            "description": "A comprehensive solution",
            "approach": "Using best practices",
            "implementation": "Detailed implementation steps",
            "quality_score": 0.9
        }

        # Act
        with patch('devsynth.application.edrr.edrr_coordinator_enhanced.calculate_enhanced_quality_score') as mock_calculate:
            mock_calculate.return_value = 0.95
            score = mock_coordinator._calculate_quality_score(result)

        # Assert
        assert score == 0.95
