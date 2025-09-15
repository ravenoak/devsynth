from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.edrr.edrr_phase_transitions import MetricType
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.memory import MemoryType
from devsynth.methodology.base import Phase


@pytest.fixture
def memory_manager():
    """Create a mock memory manager for testing."""
    mock_memory_manager = MagicMock(spec=MemoryManager)
    mock_memory_manager.store.return_value = "memory_id_123"
    mock_memory_manager.retrieve.return_value = {
        "content": "Test memory content",
        "metadata": {"key": "value"},
    }
    mock_memory_manager.search_memory.return_value = [
        {
            "id": "memory_id_123",
            "content": "Test memory content",
            "metadata": {"key": "value"},
            "score": 0.95,
        }
    ]
    return mock_memory_manager


@pytest.fixture
def wsde_team():
    """Create a mock WSDE team for testing."""
    mock_wsde_team = MagicMock()
    mock_wsde_team.execute_task.return_value = {
        "result": "Task executed successfully",
        "artifacts": ["artifact1", "artifact2"],
        "metrics": {"time_taken": 10.5},
    }
    mock_wsde_team.get_team_report.return_value = {
        "team_composition": ["Agent1", "Agent2", "Agent3"],
        "task_distribution": {"Agent1": 2, "Agent2": 3, "Agent3": 1},
        "performance_metrics": {"efficiency": 0.85, "quality": 0.9},
    }
    mock_wsde_team.assign_roles_for_phase.return_value = None
    mock_wsde_team.get_role_map.return_value = {"Agent1": "role1", "Agent2": "role2"}
    mock_wsde_team.generate_diverse_ideas.return_value = ["idea1", "idea2"]
    mock_wsde_team.create_comparison_matrix.return_value = {
        "idea1": {"score": 0.8},
        "idea2": {"score": 0.6},
    }
    mock_wsde_team.evaluate_options.return_value = [
        {"option": "idea1", "score": 0.8},
        {"option": "idea2", "score": 0.6},
    ]
    mock_wsde_team.analyze_trade_offs.return_value = [
        {"option1": "idea1", "option2": "idea2", "trade_off": "complexity vs speed"}
    ]
    mock_wsde_team.formulate_decision_criteria.return_value = {
        "criteria1": 0.7,
        "criteria2": 0.3,
    }
    mock_wsde_team.select_best_option.return_value = {"option": "idea1", "score": 0.8}
    mock_wsde_team.elaborate_details.return_value = {
        "option": "idea1",
        "details": "detailed implementation",
    }
    mock_wsde_team.create_implementation_plan.return_value = [
        {"step": 1, "description": "step 1"}
    ]
    mock_wsde_team.optimize_implementation.return_value = [
        {"step": 1, "description": "optimized step 1"}
    ]
    mock_wsde_team.perform_quality_assurance.return_value = {
        "passed": True,
        "issues": [],
    }
    mock_wsde_team.get_primus.return_value = "Agent1"
    mock_wsde_team.conduct_peer_review.return_value = {
        "reviewer": "Agent2",
        "comments": "looks good",
    }
    mock_wsde_team.extract_learnings.return_value = [
        {"category": "technical", "learning": "learning1"}
    ]
    mock_wsde_team.recognize_patterns.return_value = [
        {"pattern": "pattern1", "frequency": 0.7}
    ]
    mock_wsde_team.integrate_knowledge.return_value = {
        "status": "success",
        "integrated_items": 3,
    }
    mock_wsde_team.generate_improvement_suggestions.return_value = [
        {"phase": "EXPAND", "suggestion": "suggestion1"}
    ]
    return mock_wsde_team


@pytest.fixture
def code_analyzer():
    """Create a mock code analyzer for testing."""
    mock_code_analyzer = MagicMock(spec=CodeAnalyzer)
    mock_code_analyzer.analyze_code.return_value = {
        "complexity": 5,
        "maintainability": 8,
        "issues": ["Issue1", "Issue2"],
    }
    return mock_code_analyzer


@pytest.fixture
def ast_transformer():
    """Create a mock AST transformer for testing."""
    mock_ast_transformer = MagicMock(spec=AstTransformer)
    return mock_ast_transformer


@pytest.fixture
def prompt_manager():
    """Create a mock prompt manager for testing."""
    mock_prompt_manager = MagicMock(spec=PromptManager)
    return mock_prompt_manager


@pytest.fixture
def documentation_manager():
    """Create a mock documentation manager for testing."""
    mock_documentation_manager = MagicMock(spec=DocumentationManager)
    return mock_documentation_manager


@pytest.fixture
def enhanced_coordinator(
    memory_manager,
    wsde_team,
    code_analyzer,
    ast_transformer,
    prompt_manager,
    documentation_manager,
):
    """Create an EnhancedEDRRCoordinator instance for testing."""
    coordinator = EnhancedEDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=code_analyzer,
        ast_transformer=ast_transformer,
        prompt_manager=prompt_manager,
        documentation_manager=documentation_manager,
        enable_enhanced_logging=True,
    )
    return coordinator


class TestEnhancedEDRRCoordinator:
    """Tests for the EnhancedEDRRCoordinator class.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_initialization_succeeds(self, enhanced_coordinator):
        """Test that the enhanced coordinator initializes correctly.

        ReqID: N/A"""
        assert enhanced_coordinator is not None
        assert enhanced_coordinator.memory_manager is not None
        assert enhanced_coordinator.wsde_team is not None
        assert enhanced_coordinator.code_analyzer is not None
        assert enhanced_coordinator.ast_transformer is not None
        assert enhanced_coordinator.prompt_manager is not None
        assert enhanced_coordinator.documentation_manager is not None
        assert enhanced_coordinator._enable_enhanced_logging is True
        assert enhanced_coordinator.recursion_depth == 0
        assert enhanced_coordinator.parent_cycle_id is None
        assert enhanced_coordinator.parent_phase is None
        assert hasattr(enhanced_coordinator, "phase_metrics")
        from devsynth.application.edrr.edrr_phase_transitions import (
            PhaseTransitionMetrics,
        )

        assert isinstance(enhanced_coordinator.phase_metrics, PhaseTransitionMetrics)

    @pytest.mark.medium
    def test_progress_to_phase_has_expected(self, enhanced_coordinator, memory_manager):
        """Test enhanced progress to phase with metrics collection.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        enhanced_coordinator.start_cycle(task)
        with patch.object(
            enhanced_coordinator, "_safe_store_with_edrr_phase"
        ) as mock_store:
            with patch(
                "devsynth.application.edrr.edrr_coordinator_enhanced."
                "collect_phase_metrics"
            ) as mock_collect_metrics:
                mock_collect_metrics.return_value = {
                    "duration": 10.5,
                    "quality": 0.85,
                    "completeness": 0.8,
                    "consistency": 0.75,
                }
                enhanced_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
                assert enhanced_coordinator.current_phase == Phase.DIFFERENTIATE
                mock_collect_metrics.assert_called_once()
                mock_store.assert_called_with(
                    mock_collect_metrics.return_value,
                    MemoryType.EPISODIC,
                    Phase.DIFFERENTIATE.value,
                    {
                        "cycle_id": enhanced_coordinator.cycle_id,
                        "type": "PHASE_METRICS",
                    },
                )

    @pytest.mark.medium
    def test_enhanced_decide_next_phase_has_expected(self, enhanced_coordinator):
        """Test the enhanced decision-making for the next phase.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        enhanced_coordinator.start_cycle(task)
        enhanced_coordinator.auto_phase_transitions = True
        enhanced_coordinator.quality_based_transitions = True
        enhanced_coordinator.phase_metrics.end_phase(
            Phase.EXPAND,
            {
                "duration": 10.5,
                "quality": 0.85,
                "completeness": 0.8,
                "consistency": 0.75,
            },
        )
        with patch.object(
            enhanced_coordinator.phase_metrics, "should_transition"
        ) as mock_should_transition:
            mock_should_transition.return_value = (
                True,
                {"reason": "High quality metrics"},
            )
            next_phase = enhanced_coordinator._enhanced_decide_next_phase()
            assert next_phase == Phase.DIFFERENTIATE
            mock_should_transition.return_value = (
                False,
                {"reason": "Low quality metrics"},
            )
            enhanced_coordinator.results[Phase.EXPAND.name] = {"phase_complete": True}
            next_phase = enhanced_coordinator._enhanced_decide_next_phase()
            assert next_phase == Phase.DIFFERENTIATE
            enhanced_coordinator.results[Phase.EXPAND.name] = {"phase_complete": False}
            next_phase = enhanced_coordinator._enhanced_decide_next_phase()
            assert next_phase is None

    @pytest.mark.medium
    def test_phase_failure_hook_called(self, enhanced_coordinator):
        """Failure hooks run when phase cannot transition.

        ReqID: N/A"""
        task = {"name": "t"}
        enhanced_coordinator.start_cycle(task)
        metrics = {
            MetricType.QUALITY.value: 0.2,
            MetricType.COMPLETENESS.value: 0.6,
            MetricType.CONSISTENCY.value: 0.6,
            MetricType.CONFLICTS.value: 0,
        }
        enhanced_coordinator.phase_metrics.metrics[Phase.EXPAND.name] = metrics
        called = {}

        def hook(m):
            called["called"] = True

        enhanced_coordinator.register_phase_failure_hook(Phase.EXPAND, hook)
        next_phase = enhanced_coordinator._enhanced_decide_next_phase()
        assert called.get("called") is True
        assert next_phase is None

    @pytest.mark.medium
    def test_enhanced_maybe_auto_progress_succeeds(self, enhanced_coordinator):
        """Test the enhanced auto-progression.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        enhanced_coordinator.start_cycle(task)
        enhanced_coordinator.auto_phase_transitions = True
        with patch.object(
            enhanced_coordinator, "_enhanced_decide_next_phase"
        ) as mock_decide:
            mock_decide.side_effect = [Phase.DIFFERENTIATE, None]
            with patch.object(EDRRCoordinator, "progress_to_phase") as mock_progress:
                enhanced_coordinator._enhanced_maybe_auto_progress()
                assert mock_decide.call_count == 2
                mock_progress.assert_called_once_with(Phase.DIFFERENTIATE)
        enhanced_coordinator.auto_phase_transitions = False
        with patch.object(
            enhanced_coordinator, "_enhanced_decide_next_phase"
        ) as mock_decide:
            enhanced_coordinator._enhanced_maybe_auto_progress()
            mock_decide.assert_not_called()

    @pytest.mark.medium
    def test_calculate_quality_score_succeeds(self, enhanced_coordinator):
        """Test the quality score calculation.

        ReqID: N/A"""
        result = {
            "result": "Task executed successfully",
            "artifacts": ["artifact1", "artifact2"],
            "metrics": {"time_taken": 10.5, "quality": 0.85, "complexity": 5},
        }
        score = enhanced_coordinator._calculate_quality_score(result)
        assert isinstance(score, float)
        assert 0 <= score <= 1
        result_no_metrics = {
            "result": "Task executed successfully",
            "artifacts": ["artifact1", "artifact2"],
        }
        score = enhanced_coordinator._calculate_quality_score(result_no_metrics)
        assert isinstance(score, float)
        assert 0 <= score <= 1

    @pytest.mark.medium
    def test_get_phase_metrics_has_expected(self, enhanced_coordinator):
        """Test getting metrics for a specific phase.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        enhanced_coordinator.start_cycle(task)
        expand_metrics = {
            "duration": 10.5,
            "quality": 0.85,
            "completeness": 0.8,
            "consistency": 0.75,
        }
        differentiate_metrics = {
            "duration": 15.2,
            "quality": 0.9,
            "completeness": 0.85,
            "consistency": 0.8,
        }
        enhanced_coordinator.phase_metrics.end_phase(Phase.EXPAND, expand_metrics)
        enhanced_coordinator.phase_metrics.end_phase(
            Phase.DIFFERENTIATE, differentiate_metrics
        )
        with patch.object(
            enhanced_coordinator.phase_metrics, "get_phase_metrics"
        ) as mock_get_metrics:
            mock_get_metrics.return_value = expand_metrics
            metrics = enhanced_coordinator.get_phase_metrics(Phase.EXPAND)
            mock_get_metrics.assert_called_once_with(Phase.EXPAND)
            assert metrics == expand_metrics
            mock_get_metrics.reset_mock()
            mock_get_metrics.return_value = differentiate_metrics
            enhanced_coordinator.current_phase = Phase.DIFFERENTIATE
            metrics = enhanced_coordinator.get_phase_metrics()
            mock_get_metrics.assert_called_once_with(Phase.DIFFERENTIATE)
            assert metrics == differentiate_metrics
            mock_get_metrics.reset_mock()
            mock_get_metrics.return_value = {}
            metrics = enhanced_coordinator.get_phase_metrics(Phase.REFINE)
            mock_get_metrics.assert_called_once_with(Phase.REFINE)
            assert metrics == {}

    @pytest.mark.medium
    def test_get_all_metrics_has_expected(self, enhanced_coordinator):
        """Test getting all phase metrics.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        enhanced_coordinator.start_cycle(task)
        expected_metrics = {
            Phase.EXPAND.name: {
                "duration": 10.5,
                "quality": 0.85,
                "completeness": 0.8,
                "consistency": 0.75,
            },
            Phase.DIFFERENTIATE.name: {
                "duration": 15.2,
                "quality": 0.9,
                "completeness": 0.85,
                "consistency": 0.8,
            },
        }
        with patch.object(
            enhanced_coordinator.phase_metrics, "get_all_metrics"
        ) as mock_get_all_metrics:
            mock_get_all_metrics.return_value = expected_metrics
            all_metrics = enhanced_coordinator.get_all_metrics()
            mock_get_all_metrics.assert_called_once()
            assert all_metrics == expected_metrics

    @pytest.mark.medium
    def test_get_metrics_history_has_expected(self, enhanced_coordinator):
        """Test getting metrics history from the PhaseTransitionMetrics.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        enhanced_coordinator.start_cycle(task)
        expected_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "phase": Phase.EXPAND.name,
                "action": "start",
                "metrics": {},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": Phase.EXPAND.name,
                "action": "end",
                "metrics": {
                    "duration": 10.5,
                    "quality": 0.85,
                    "completeness": 0.8,
                    "consistency": 0.75,
                },
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": Phase.DIFFERENTIATE.name,
                "action": "start",
                "metrics": {},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "phase": Phase.DIFFERENTIATE.name,
                "action": "end",
                "metrics": {
                    "duration": 15.2,
                    "quality": 0.9,
                    "completeness": 0.85,
                    "consistency": 0.8,
                },
            },
        ]
        with patch.object(
            enhanced_coordinator.phase_metrics, "get_history"
        ) as mock_get_history:
            mock_get_history.return_value = expected_history
            history = enhanced_coordinator.get_metrics_history()
            mock_get_history.assert_called_once()
            assert history == expected_history
            assert isinstance(history, list)
            assert len(history) == 4
            assert "timestamp" in history[0]
            assert "phase" in history[0]
            assert "action" in history[0]
            assert "metrics" in history[0]

    @pytest.mark.medium
    def test_create_micro_cycle_succeeds(self, enhanced_coordinator):
        """Test creating a micro-cycle with enhanced features.

        ReqID: N/A"""
        task = {
            "name": "Test Task",
            "description": "This is a test task",
            "requirements": ["req1", "req2"],
        }
        enhanced_coordinator.start_cycle(task)
        enhanced_coordinator.current_phase = Phase.DIFFERENTIATE
        micro_task = {
            "name": "Micro Task",
            "description": "This is a micro task",
            "requirements": ["micro_req1"],
        }
        with patch.object(
            enhanced_coordinator, "should_terminate_recursion", return_value=(False, "")
        ) as mock_should_terminate:
            with patch(
                "devsynth.application.edrr.edrr_coordinator_enhanced."
                "EnhancedEDRRCoordinator"
            ) as mock_constructor:
                mock_micro_coordinator = MagicMock()
                mock_constructor.return_value = mock_micro_coordinator
                result = enhanced_coordinator.create_micro_cycle(
                    micro_task, Phase.DIFFERENTIATE
                )
                mock_should_terminate.assert_called_once_with(micro_task)
                mock_constructor.assert_called_once_with(
                    memory_manager=enhanced_coordinator.memory_manager,
                    wsde_team=enhanced_coordinator.wsde_team,
                    code_analyzer=enhanced_coordinator.code_analyzer,
                    ast_transformer=enhanced_coordinator.ast_transformer,
                    prompt_manager=enhanced_coordinator.prompt_manager,
                    documentation_manager=enhanced_coordinator.documentation_manager,
                    enable_enhanced_logging=(
                        enhanced_coordinator._enable_enhanced_logging
                    ),
                    parent_cycle_id=enhanced_coordinator.cycle_id,
                    recursion_depth=enhanced_coordinator.recursion_depth + 1,
                    parent_phase=Phase.DIFFERENTIATE,
                    config=enhanced_coordinator.config,
                )
                mock_micro_coordinator.start_cycle.assert_called_once_with(micro_task)
                assert result == mock_micro_coordinator


@pytest.mark.fast
def test_enhanced_decide_next_phase_respects_auto_phase(enhanced_coordinator):
    """Quality metrics guide automatic transitions.

    ReqID: N/A"""
    enhanced_coordinator.current_phase = Phase.EXPAND
    enhanced_coordinator.results = {Phase.EXPAND.name: {}}
    enhanced_coordinator.auto_phase_transitions = True
    enhanced_coordinator.quality_based_transitions = True
    enhanced_coordinator.phase_metrics.should_transition = MagicMock(
        return_value=(True, {})
    )

    next_phase = enhanced_coordinator._enhanced_decide_next_phase()
    assert next_phase == Phase.DIFFERENTIATE

    enhanced_coordinator.auto_phase_transitions = False
    assert enhanced_coordinator._enhanced_decide_next_phase() is None
