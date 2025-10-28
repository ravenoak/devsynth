"""
Unit tests for enhanced EDRR phase transitions.

This module contains unit tests for the enhanced phase transition functionality
in the EDRR framework, including quality scoring, metrics collection, and
automatic phase transitions.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.edrr.edrr_phase_transitions import (
    MetricType,
    PhaseTransitionMetrics,
    QualityThreshold,
    calculate_enhanced_quality_score,
    collect_phase_metrics,
)
from devsynth.methodology.base import Phase


class TestPhaseTransitionMetrics:
    """Test suite for PhaseTransitionMetrics class.

    ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.metrics = PhaseTransitionMetrics()

    @pytest.mark.medium
    def test_start_phase_has_expected(self):
        """Test recording the start of a phase.

        ReqID: N/A"""
        self.metrics.start_phase(Phase.EXPAND)
        assert Phase.EXPAND.name in self.metrics.start_times
        assert len(self.metrics.history) == 1
        assert self.metrics.history[0]["phase"] == Phase.EXPAND.name
        assert self.metrics.history[0]["action"] == "start"

    @pytest.mark.medium
    def test_end_phase_has_expected(self):
        """Test recording the end of a phase with metrics.

        ReqID: N/A"""
        self.metrics.start_phase(Phase.EXPAND)
        test_metrics = {
            "quality": 0.8,
            "completeness": 0.7,
            "consistency": 0.9,
            "conflicts": 0,
        }
        self.metrics.end_phase(Phase.EXPAND, test_metrics)
        assert Phase.EXPAND.name in self.metrics.metrics
        assert self.metrics.metrics[Phase.EXPAND.name] == test_metrics
        assert len(self.metrics.history) == 2
        assert self.metrics.history[1]["phase"] == Phase.EXPAND.name
        assert self.metrics.history[1]["action"] == "end"
        assert self.metrics.history[1]["metrics"] == test_metrics

    @pytest.mark.medium
    def test_should_transition_all_thresholds_met_succeeds(self):
        """Test should_transition when all thresholds are met.

        ReqID: N/A"""
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1,
        }
        self.metrics.metrics[phase.name] = metrics
        should_transition, reasons = self.metrics.should_transition(phase)
        assert should_transition is True
        assert all(
                "Meets threshold" in reason or "within threshold" in reason
                for reason in reasons.values()
        )

    @pytest.mark.medium
    def test_should_transition_some_thresholds_not_met_succeeds(self):
        """Test should_transition when some thresholds are not met.

        ReqID: N/A"""
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1,
        }
        self.metrics.metrics[phase.name] = metrics
        should_transition, reasons = self.metrics.should_transition(phase)
        assert should_transition is False
        assert "Below threshold" in reasons[MetricType.QUALITY.value]

    @pytest.mark.medium
    def test_should_transition_missing_metrics_succeeds(self):
        """Test should_transition when metrics are missing.

        ReqID: N/A"""
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1,
        }
        self.metrics.metrics[phase.name] = metrics
        should_transition, reasons = self.metrics.should_transition(phase)
        assert should_transition is False
        assert "Missing metric" in reasons[MetricType.COMPLETENESS.value]

    @pytest.mark.medium
    def test_should_transition_too_many_conflicts_succeeds(self):
        """Test should_transition when there are too many conflicts.

        ReqID: N/A"""
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 5,
        }
        self.metrics.metrics[phase.name] = metrics
        should_transition, reasons = self.metrics.should_transition(phase)
        assert should_transition is False
        assert "Too many conflicts" in reasons[MetricType.CONFLICTS.value]

    @pytest.mark.medium
    def test_configure_thresholds_override(self):
        """Custom thresholds affect transition decisions.

        ReqID: N/A"""
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: 0.85,
            MetricType.COMPLETENESS.value: 0.9,
            MetricType.CONSISTENCY.value: 0.9,
            MetricType.CONFLICTS.value: 0,
        }
        self.metrics.metrics[phase.name] = metrics
        self.metrics.configure_thresholds(phase, {MetricType.QUALITY.value: 0.9})
        should_transition, _ = self.metrics.should_transition(phase)
        assert should_transition is False
        self.metrics.configure_thresholds(phase, {MetricType.QUALITY.value: 0.8})
        should_transition, _ = self.metrics.should_transition(phase)
        assert should_transition is True

    @pytest.mark.medium
    def test_should_transition_recovery_hook_recovers(self):
        """Recovery hooks adjust metrics to allow transition.",

        ReqID: N/A"""
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.2,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1,
        }
        self.metrics.metrics[phase.name] = metrics

        def hook(m):
            m[MetricType.QUALITY.value] = 0.9
            return {"recovered": True}

        self.metrics.register_recovery_hook(phase, hook)
        should_transition, reasons = self.metrics.should_transition(phase)
        assert should_transition is True
        assert reasons["recovery"] == "metrics recovered"

    @pytest.mark.medium
    def test_should_transition_recovery_hook_fails(self):
        """Recovery hooks that fail keep transition blocked.",

        ReqID: N/A"""
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.2,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1,
        }
        self.metrics.metrics[phase.name] = metrics

        def hook(_m):
            return {"recovered": False}

        self.metrics.register_recovery_hook(phase, hook)
        should_transition, reasons = self.metrics.should_transition(phase)
        assert should_transition is False
        assert reasons["recovery"] == "recovery hooks did not recover"

    @pytest.mark.medium
    def test_failure_hook_invoked_on_unrecovered_failure(self):
        """Failure hooks run when recovery does not resolve issues.

        ReqID: N/A"""
        phase = Phase.EXPAND
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.2,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1,
        }
        self.metrics.metrics[phase.name] = metrics

        self.metrics.register_recovery_hook(phase, lambda _m: {"recovered": False})
        called = {}

        def failure_hook(m):
            called["metrics"] = m.copy()

        self.metrics.register_failure_hook(phase, failure_hook)
        self.metrics.should_transition(phase)
        assert (
            called["metrics"][MetricType.QUALITY.value]
            == metrics[MetricType.QUALITY.value]
        )


class TestQualityScoring:
    """Test suite for quality scoring functions.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_calculate_enhanced_quality_score_non_dict_succeeds(self):
        """Test calculating quality score for non-dictionary results.

        ReqID: N/A"""
        result = "This is a string result"
        score = calculate_enhanced_quality_score(result)
        assert score == 0.5

    @pytest.mark.medium
    def test_calculate_enhanced_quality_score_empty_dict_succeeds(self):
        """Test calculating quality score for empty dictionary results.

        ReqID: N/A"""
        result = {}
        score = calculate_enhanced_quality_score(result)
        assert score > 0
        assert score < 0.5

    @pytest.mark.medium
    def test_calculate_enhanced_quality_score_good_result_succeeds(self):
        """Test calculating quality score for a good result.

        ReqID: N/A"""
        result = {
            "description": "A comprehensive solution",
            "approach": "Using best practices",
            "implementation": "Detailed implementation steps",
            "analysis": "Thorough analysis of the solution",
            "solution": "Complete solution with error handling",
            "quality_score": 0.9,
        }
        score = calculate_enhanced_quality_score(result)
        assert score > 0.7

    @pytest.mark.medium
    def test_calculate_enhanced_quality_score_with_errors(self):
        """Test calculating quality score for a result with errors.

        ReqID: N/A"""
        result = {
            "description": "A solution with issues",
            "approach": "Using some practices",
            "implementation": "Implementation steps",
            "error": "There was an error in the implementation",
        }
        score = calculate_enhanced_quality_score(result)
        assert score < 0.7

    @pytest.mark.medium
    def test_collect_phase_metrics_expand_phase_has_expected(self):
        """Test collecting metrics for the Expand phase.

        ReqID: N/A"""
        results = {
            "result1": {"ideas": ["Idea 1", "Idea 2", "Idea 3"], "quality_score": 0.8},
            "result2": {
                "approaches": ["Approach 1", "Approach 2"],
                "quality_score": 0.7,
            },
        }
        metrics = collect_phase_metrics(Phase.EXPAND, results)
        assert MetricType.QUALITY.value in metrics
        assert MetricType.COMPLETENESS.value in metrics
        assert MetricType.CONSISTENCY.value in metrics
        assert MetricType.CONFLICTS.value in metrics
        assert "idea_diversity" in metrics

    @pytest.mark.medium
    def test_collect_phase_metrics_differentiate_phase_has_expected(self):
        """Test collecting metrics for the Differentiate phase.

        ReqID: N/A"""
        results = {
            "result1": {
                "categories": {
                    "category1": ["Item 1", "Item 2"],
                    "category2": ["Item 3", "Item 4"],
                },
                "quality_score": 0.8,
            }
        }
        metrics = collect_phase_metrics(Phase.DIFFERENTIATE, results)
        assert MetricType.QUALITY.value in metrics
        assert MetricType.COMPLETENESS.value in metrics
        assert MetricType.CONSISTENCY.value in metrics
        assert MetricType.CONFLICTS.value in metrics
        assert "categorization_quality" in metrics

    @pytest.mark.medium
    def test_collect_phase_metrics_refine_phase_has_expected(self):
        """Test collecting metrics for the Refine phase.

        ReqID: N/A"""
        results = {
            "result1": {
                "code": '\n                def test_function():\n                    # This is a comment\n                    try:\n                        return "Hello, world!"\n                    except Exception as e:\n                        return str(e)\n                ',
                "test_coverage": 80,
                "quality_score": 0.8,
            }
        }
        metrics = collect_phase_metrics(Phase.REFINE, results)
        assert MetricType.QUALITY.value in metrics
        assert MetricType.COMPLETENESS.value in metrics
        assert MetricType.CONSISTENCY.value in metrics
        assert MetricType.CONFLICTS.value in metrics
        assert MetricType.COVERAGE.value in metrics
        assert "code_quality" in metrics

    @pytest.mark.medium
    def test_collect_phase_metrics_retrospect_phase_has_expected(self):
        """Test collecting metrics for the Retrospect phase.

        ReqID: N/A"""
        results = {
            "result1": {
                "learnings": ["Learning 1", "Learning 2"],
                "improvements": ["Improvement 1", "Improvement 2"],
                "successes": ["Success 1", "Success 2"],
                "challenges": ["Challenge 1", "Challenge 2"],
                "next_steps": ["Next step 1", "Next step 2"],
                "quality_score": 0.9,
            }
        }
        metrics = collect_phase_metrics(Phase.RETROSPECT, results)
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
            "result1": {"ideas": ["Idea 1", "Idea 2"], "quality_score": 0.8}
        }
    }
    coordinator.phase_metrics = PhaseTransitionMetrics()
    coordinator._phase_start_times = {Phase.EXPAND: datetime.now() - timedelta(hours=1)}
    coordinator.auto_phase_transitions = True
    coordinator.quality_based_transitions = True
    coordinator.phase_transition_timeout = 3600
    return coordinator


class TestEnhancedEDRRCoordinator:
    """Test suite for EnhancedEDRRCoordinator class.

    ReqID: N/A"""

    @patch("devsynth.application.edrr.edrr_coordinator_enhanced.collect_phase_metrics")
    @pytest.mark.medium
    def test_progress_to_phase_collects_metrics_has_expected(
        self, mock_collect_metrics, mock_coordinator
    ):
        """Test that progress_to_phase collects metrics.

        ReqID: N/A"""
        mock_collect_metrics.return_value = {
            "quality": 0.8,
            "completeness": 0.7,
            "consistency": 0.9,
            "conflicts": 0,
        }
        mock_coordinator.progress_to_phase = (
            EnhancedEDRRCoordinator.progress_to_phase.__get__(mock_coordinator)
        )
        mock_coordinator._safe_store_with_edrr_phase = MagicMock()
        mock_coordinator._enhanced_maybe_auto_progress = MagicMock()
        mock_coordinator.phase_metrics = MagicMock()
        mock_coordinator.phase_metrics.start_phase = MagicMock()
        mock_coordinator.phase_metrics.end_phase = MagicMock()
        mock_coordinator.results = {Phase.DIFFERENTIATE.name: {}}
        mock_coordinator.cycle_id = "test_cycle_id"
        with patch(
            "devsynth.application.edrr.edrr_coordinator_enhanced.super"
        ) as mock_super:
            mock_super.return_value.progress_to_phase = MagicMock()
            try:
                mock_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
            except Exception as e:
                print(f"Exception in test_progress_to_phase_collects_metrics: {e}")
                raise
        mock_collect_metrics.assert_called_once()
        mock_coordinator.phase_metrics.start_phase.assert_called_once_with(
            Phase.DIFFERENTIATE
        )
        mock_coordinator.phase_metrics.end_phase.assert_called_once()
        mock_coordinator._safe_store_with_edrr_phase.assert_called_once()
        mock_coordinator._enhanced_maybe_auto_progress.assert_called_once()

    @pytest.mark.medium
    def test_enhanced_decide_next_phase_quality_based_has_expected(
        self, mock_coordinator
    ):
        """Test that _enhanced_decide_next_phase considers quality metrics.

        ReqID: N/A"""
        mock_coordinator._enhanced_decide_next_phase = (
            EnhancedEDRRCoordinator._enhanced_decide_next_phase.__get__(
                mock_coordinator
            )
        )
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value + 0.1,
            MetricType.CONFLICTS.value: 1,
        }
        mock_coordinator.phase_metrics.metrics[Phase.EXPAND.name] = metrics
        next_phase = mock_coordinator._enhanced_decide_next_phase()
        assert next_phase == Phase.DIFFERENTIATE

    @pytest.mark.medium
    def test_enhanced_decide_next_phase_timeout_based_has_expected(
        self, mock_coordinator
    ):
        """Test that _enhanced_decide_next_phase considers timeouts.

        ReqID: N/A"""
        mock_coordinator._enhanced_decide_next_phase = (
            EnhancedEDRRCoordinator._enhanced_decide_next_phase.__get__(
                mock_coordinator
            )
        )
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value - 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value - 0.1,
            MetricType.CONFLICTS.value: 4,
        }
        mock_coordinator.phase_metrics.metrics[Phase.EXPAND.name] = metrics
        mock_coordinator.phase_transition_timeout = 1
        next_phase = mock_coordinator._enhanced_decide_next_phase()
        assert next_phase == Phase.DIFFERENTIATE

    @pytest.mark.medium
    def test_enhanced_decide_next_phase_no_transition_returns_expected_result(
        self, mock_coordinator
    ):
        """Test that _enhanced_decide_next_phase returns None when no transition should occur.

        ReqID: N/A"""
        mock_coordinator._enhanced_decide_next_phase = (
            EnhancedEDRRCoordinator._enhanced_decide_next_phase.__get__(
                mock_coordinator
            )
        )
        metrics = {
            MetricType.QUALITY.value: QualityThreshold.MEDIUM.value - 0.1,
            MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value - 0.1,
            MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value - 0.1,
            MetricType.CONFLICTS.value: 4,
        }
        mock_coordinator.phase_metrics.metrics[Phase.EXPAND.name] = metrics
        mock_coordinator.phase_transition_timeout = 86400
        mock_coordinator._phase_start_times[Phase.EXPAND] = datetime.now()
        next_phase = mock_coordinator._enhanced_decide_next_phase()
        assert next_phase is None

    @pytest.mark.medium
    def test_enhanced_maybe_auto_progress_has_expected(self, mock_coordinator):
        """Test that _enhanced_maybe_auto_progress calls progress_to_phase when conditions are met and has safeguards against infinite loops.

        ReqID: N/A"""
        mock_coordinator._enhanced_maybe_auto_progress = (
            EnhancedEDRRCoordinator._enhanced_maybe_auto_progress.__get__(
                mock_coordinator
            )
        )
        mock_decide_next = MagicMock()
        mock_decide_next.side_effect = [Phase.DIFFERENTIATE, None]
        mock_coordinator._enhanced_decide_next_phase = mock_decide_next
        mock_coordinator.auto_phase_transitions = True
        mock_coordinator.current_phase = Phase.EXPAND
        mock_coordinator.results = {}
        mock_coordinator.phase_metrics = MagicMock()
        with patch(
            "devsynth.application.edrr.edrr_coordinator_enhanced.EDRRCoordinator.progress_to_phase"
        ) as mock_super_progress:
            mock_coordinator._enhanced_maybe_auto_progress()
            assert mock_coordinator._enhanced_decide_next_phase.call_count == 2
            mock_super_progress.assert_called_once_with(Phase.DIFFERENTIATE)
            assert not getattr(mock_coordinator, "_in_auto_progress", False)

    @pytest.mark.medium
    def test_enhanced_maybe_auto_progress_reentry_prevention_succeeds(
        self, mock_coordinator
    ):
        """Test that _enhanced_maybe_auto_progress prevents re-entry during active transition.

        ReqID: N/A"""
        mock_coordinator._enhanced_maybe_auto_progress = (
            EnhancedEDRRCoordinator._enhanced_maybe_auto_progress.__get__(
                mock_coordinator
            )
        )
        mock_coordinator._enhanced_decide_next_phase = MagicMock(
            return_value=Phase.DIFFERENTIATE
        )
        mock_coordinator._in_auto_progress = True
        mock_coordinator._enhanced_maybe_auto_progress()
        mock_coordinator._enhanced_decide_next_phase.assert_not_called()

    @pytest.mark.medium
    def test_enhanced_maybe_auto_progress_max_iterations_succeeds(
        self, mock_coordinator
    ):
        """Test that _enhanced_maybe_auto_progress respects maximum iteration count.

        ReqID: N/A"""
        mock_coordinator._enhanced_maybe_auto_progress = (
            EnhancedEDRRCoordinator._enhanced_maybe_auto_progress.__get__(
                mock_coordinator
            )
        )
        mock_coordinator._enhanced_decide_next_phase = MagicMock(
            return_value=Phase.DIFFERENTIATE
        )
        with patch(
            "devsynth.application.edrr.edrr_coordinator_enhanced.EDRRCoordinator.progress_to_phase"
        ) as mock_super_progress:
            mock_coordinator.phase_metrics = MagicMock()
            mock_coordinator.phase_metrics.end_phase = MagicMock()
            mock_coordinator.results = {}
            mock_coordinator._enhanced_maybe_auto_progress()
            assert mock_coordinator._enhanced_decide_next_phase.call_count <= 4
            assert mock_super_progress.call_count <= 4

    @pytest.mark.medium
    def test_calculate_quality_score_succeeds(self, mock_coordinator):
        """Test that _calculate_quality_score uses the enhanced quality scoring.

        ReqID: N/A"""
        mock_coordinator._calculate_quality_score = (
            EnhancedEDRRCoordinator._calculate_quality_score.__get__(mock_coordinator)
        )
        result = {
            "description": "A comprehensive solution",
            "approach": "Using best practices",
            "implementation": "Detailed implementation steps",
            "quality_score": 0.9,
        }
        with patch(
            "devsynth.application.edrr.edrr_coordinator_enhanced.calculate_enhanced_quality_score"
        ) as mock_calculate:
            mock_calculate.return_value = 0.95
            score = mock_coordinator._calculate_quality_score(result)
        assert score == 0.95
